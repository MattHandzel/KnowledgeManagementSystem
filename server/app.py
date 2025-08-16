import os
import sys
from pathlib import Path
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
import yaml
import subprocess

sys.path.append(str(Path(__file__).resolve().parent.parent))
from markdown_writer import SafeMarkdownWriter

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def load_config():
    cfg_path = Path(__file__).resolve().parent.parent / "config.yaml"
    if not cfg_path.exists():
        return {}
    with cfg_path.open("r") as f:
        return yaml.safe_load(f) or {}

def normalize_config(cfg):
    v = cfg.get("vault", {})
    d = {
        "vault": {
            "path": os.path.expanduser(v.get("path") or "~/notes"),
            "capture_dir": v.get("capture_dir") or "capture/raw_capture",
            "media_dir": v.get("media_dir") or "capture/raw_capture/media",
        },
        "ui": cfg.get("ui", {}),
        "capture": cfg.get("capture", {}),
        "keybindings": cfg.get("keybindings", {}),
    }
    return d

@app.get("/api/config")
def api_config():
    cfg = normalize_config(load_config())
    return cfg

@app.get("/api/clipboard")
def api_clipboard():
    """Get current clipboard content."""
    try:
        result = subprocess.run(['wl-paste', '-t', 'text'], 
                              capture_output=True, text=True, timeout=2)
        if result.returncode == 0:
            return {"content": result.stdout, "type": "text"}
        return {"content": "", "type": "text"}
    except Exception:
        return {"content": "", "type": "text"}

@app.post("/api/screenshot")
def api_screenshot():
    """Trigger grim screenshot capture."""
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
        cfg = normalize_config(load_config())
        media_dir = Path(cfg["vault"]["path"]).expanduser() / cfg["vault"]["media_dir"]
        media_dir.mkdir(parents=True, exist_ok=True)
        screenshot_path = media_dir / f"{timestamp}_screenshot.png"
        
        result = subprocess.run(['grim', str(screenshot_path)], 
                              capture_output=True, timeout=10)
        
        if result.returncode == 0:
            return {"path": str(screenshot_path), "success": True}
        return {"success": False, "error": "Screenshot failed"}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/api/capture")
async def api_capture(
    content: str = Form(""),
    context: str = Form(""),
    tags: str = Form(""),
    sources: str = Form(""),
    modalities: str = Form(""),
    created_date: Optional[str] = Form(None),
    last_edited_date: Optional[str] = Form(None),
    media: Optional[List[UploadFile]] = File(None),
):
    cfg = normalize_config(load_config())
    writer = SafeMarkdownWriter(str(Path(cfg["vault"]["path"]).expanduser()))
    ts = datetime.now(timezone.utc)
    ts_str = ts.replace(microsecond=0).isoformat()
    cds = created_date or ts.date().isoformat()
    les = last_edited_date or ts.date().isoformat()
    tag_list = [t.strip() for t in tags.split(",") if t.strip()] if isinstance(tags, str) else []
    src_list = [s.strip() for s in sources.split(",") if s.strip()] if isinstance(sources, str) else []
    mod_list = [m.strip() for m in modalities.split(",") if m.strip()] if isinstance(modalities, str) else []
    ctx = {}
    if context.strip():
        try:
            ctx = yaml.safe_load(context) or {}
            if not isinstance(ctx, dict):
                ctx = {"text": context}
        except Exception:
            ctx = {"text": context}
    files_meta = []
    if media:
        media_dir = Path(cfg["vault"]["path"]).expanduser() / cfg["vault"]["media_dir"]
        media_dir.mkdir(parents=True, exist_ok=True)
        for f in media:
            name = f.filename or f"upload_{datetime.now().timestamp()}"
            dest = media_dir / name
            b = await f.read()
            dest.write_bytes(b)
            files_meta.append({"path": str(dest), "name": name})
    capture = {
        "timestamp": ts,
        "content": content or "",
        "context": ctx,
        "tags": tag_list,
        "modalities": mod_list or ["text"],
        "sources": src_list,
        "media_files": files_meta,
        "created_date": cds,
        "last_edited_date": les,
    }
    p = writer.write_capture(capture)
    return JSONResponse({"saved_to": str(p)})

if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=int(os.environ.get("PORT", "5174")), reload=True)

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
    writer = SafeMarkdownWriter(Path(cfg["vault"]["path"]).expanduser())
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

    has_text = "text" in capture["modalities"] and bool((capture["content"] or "").strip())
    has_media = bool(capture["media_files"])
    has_clipboard = bool(capture.get("clipboard", ""))

    if not capture["modalities"] or not (has_text or has_media or has_clipboard):
        return JSONResponse({"error": "Nothing to save: select a modality or provide content"}, status_code=400)

    p = writer.write_capture(capture)
    return JSONResponse({"saved_to": str(p)})

if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=int(os.environ.get("PORT", "5174")), reload=True)

import os
import sys
from pathlib import Path
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import threading
import asyncio
from hypercorn.config import Config
from hypercorn.asyncio import serve
import yaml
import subprocess

sys.path.append(str(Path(__file__).resolve().parent.parent))
from markdown_writer import SafeMarkdownWriter
from geolocation import get_device_location
from main_db import MainDatabase

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

main_db = MainDatabase("main.db")

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

def _validate_modalities_have_content(capture_data, modalities):
    """Validate that selected modalities have actual content."""
    print(f"DEBUG: Validating modalities: {modalities}")
    print(f"DEBUG: Capture data keys: {list(capture_data.keys())}")
    print(f"DEBUG: Content value: '{capture_data.get('content', '')}'")
    
    if not modalities:
        print("DEBUG: No modalities provided")
        return False
    
    for modality in modalities:
        print(f"DEBUG: Checking modality: {modality}")
        if modality == "text":
            content = capture_data.get("content", "").strip()
            print(f"DEBUG: Text content after strip: '{content}'")
            if not content:
                print("DEBUG: Text modality validation failed - no content")
                return False
        elif modality == "clipboard":
            pass
        elif modality == "screenshot":
            if not capture_data.get("media_files"):
                return False
        elif modality == "audio":
            if not capture_data.get("media_files"):
                return False
        elif modality == "system-audio":
            if not capture_data.get("media_files"):
                return False
    
    print("DEBUG: All modality validations passed")
    return True

@app.post("/api/capture")
async def api_capture(
    content: str = Form(""),
    context: str = Form(""),
    tags: str = Form(""),
    sources: str = Form(""),
    modalities: str = Form(""),
    clipboard: str = Form(""),
    screenshot_path: str = Form(""),
    screenshot_type: str = Form(""),
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
    ctx = context.strip() if context.strip() else ""
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
    
    if screenshot_path and screenshot_type:
        files_meta.append({"path": screenshot_path, "type": screenshot_type})
    location_data = get_device_location()
    
    capture = {
        "timestamp": ts,
        "content": content or "",
        "clipboard": clipboard or "",
        "context": ctx,
        "tags": tag_list,
        "modalities": mod_list or ["text"],
        "sources": src_list,
        "location": location_data,
        "media_files": files_meta,
        "created_date": cds,
        "last_edited_date": les,
    }
    
    if not _validate_modalities_have_content(capture, mod_list):
        return JSONResponse({"error": "No content provided for selected modalities"}, status_code=400)
    
    p = writer.write_capture(capture)
    
    main_db.store_capture_data(capture)
    
    return JSONResponse({"saved_to": str(p)})


@app.get("/api/suggestions/{field_type}")
def api_suggestions(field_type: str, query: str = "", limit: int = 10):
    """Get suggestions for a field type with optional query filtering."""
    if field_type not in ['tag', 'source', 'context']:
        return JSONResponse({"error": "Invalid field type"}, status_code=400)
    
    suggestions = main_db.get_suggestions(field_type, query, limit)
    return {
        "suggestions": [
            {
                "value": s.value,
                "count": s.count,
                "last_used": s.last_used.isoformat(),
                "color": s.color
            }
            for s in suggestions
        ]
    }


@app.get("/api/suggestion-exists/{field_type}")
def api_suggestion_exists(field_type: str, value: str):
    """Check if a suggestion value exists in the database."""
    if field_type not in ['tag', 'source', 'context']:
        return JSONResponse({"error": "Invalid field type"}, status_code=400)
    
    exists = main_db.suggestion_exists(value, field_type)
    return {"exists": exists}


if __name__ == "__main__":
    config = Config()
    config.bind = [f"0.0.0.0:{int(os.environ.get('PORT', '7123'))}"]
    config.use_reloader = False
    config.accesslog = "-"
    asyncio.run(serve(app, config))

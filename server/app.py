import os
import sys
import argparse
import asyncio
import subprocess
import yaml
from pathlib import Path
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any, Set

from fastapi import FastAPI, UploadFile, File, Form, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles

# Import alias suggestions module
try:
    from alias_suggestions import generate_aliases
    ALIAS_SUGGESTIONS_AVAILABLE = True
except ImportError:
    print("⚠️ Alias suggestions module not available - using basic fallback")
    ALIAS_SUGGESTIONS_AVAILABLE = False
from hypercorn.config import Config
from hypercorn.asyncio import serve

sys.path.append(str(Path(__file__).resolve().parent.parent))
from geolocation import get_device_location

# Try to import audio recorder, but make it optional
try:
    from audio_recorder import AudioRecordingManager
    AUDIO_RECORDING_AVAILABLE = True
except (ImportError, OSError) as e:
    print(f"⚠️  Audio recording disabled: {e}")
    AUDIO_RECORDING_AVAILABLE = False
    AudioRecordingManager = None

import hashlib
import json
import re
import http.client

from main_db import MainDatabase
from markdown_writer import SafeMarkdownWriter

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

web_dist_path = Path(__file__).resolve().parent.parent / "web" / "dist"
if not web_dist_path.exists():
    web_dist_path = Path(__file__).resolve().parent / "web" / "dist"

main_db = None
# Global variables to track AI-suggested tags/sources
_ai_suggested_tags = set()
_ai_suggested_sources = set()

_config_path = None
audio_manager = AudioRecordingManager() if AUDIO_RECORDING_AVAILABLE else None
_ai_cache = {}


def get_main_db():
    """Get the initialized main database instance."""
    global main_db
    if main_db is None:
        cfg = normalize_config(load_config(_config_path))
        main_db = MainDatabase(cfg["database"]["path"])
    return main_db


def load_config(config_path=None):
    if config_path:
        cfg_path = Path(config_path)
        if not cfg_path.is_absolute():
            cfg_path = Path(__file__).resolve().parent.parent / config_path
    else:
        cfg_path = Path(__file__).resolve().parent.parent / "config.yaml"

    if not cfg_path.exists():
        return {}
    with cfg_path.open("r") as f:
        return yaml.safe_load(f) or {}


def normalize_config(cfg):
    dev_config = cfg.get("development", {})
    mode = dev_config.get("mode", "prod")
    is_dev = mode == "dev"

    vault_config = cfg.get("vault", {})
    database_config = cfg.get("database", {})

    vault_path = vault_config.get("path", "~/notes")
    if vault_path == "ROOT_DIRECTORY_PATH":
        root_path = str(Path(__file__).resolve().parent.parent)
        vault_path = root_path
    elif vault_path == "ROOT_DIRECTORY_PATH/dev":
        root_path = str(Path(__file__).resolve().parent.parent)
        vault_path = root_path + "/dev"

    db_path = database_config.get("path", "server/main.db")

    if "KMS_DATA_DIR" in os.environ:
        data_dir = Path(os.environ["KMS_DATA_DIR"])
        db_path = str(data_dir / "main.db")
    elif "KMS_DB_PATH" in os.environ:
        db_path = os.environ["KMS_DB_PATH"]
    elif not Path(db_path).is_absolute():
        if mode == "prod":
            if "XDG_DATA_HOME" in os.environ:
                data_dir = Path(os.environ["XDG_DATA_HOME"]) / "kms-capture"
            else:
                data_dir = Path.home() / ".local" / "share" / "kms-capture"
            data_dir.mkdir(parents=True, exist_ok=True)
            db_path = str(data_dir / "main.db")
        else:
            db_path = str(Path(__file__).resolve().parent.parent / db_path)

    if "KMS_VAULT_PATH" in os.environ:
        vault_path = os.environ["KMS_VAULT_PATH"]

    d = {
        "vault": {
            "path": os.path.expanduser(vault_path),
            "capture_dir": vault_config.get("capture_dir") or "capture/raw_capture",
            "media_dir": vault_config.get("media_dir") or "capture/raw_capture/media",
        },
        "database": {
            "path": db_path,
        },
        "ui": cfg.get("ui", {}),
        "capture": cfg.get("capture", {}),
        "keybindings": cfg.get("keybindings", {}),
        "theme": cfg.get("theme", {}),
        "ai": cfg.get("ai", {}),
        "mode": mode,
        "is_dev": is_dev,
    }
    return d


def _kebab_case(s: str) -> str:
    s = s.strip().lower()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    s = re.sub(r"-+", "-", s)
    return s.strip("-")


def _singularize(s: str) -> str:
    t = s.strip()
    if len(t) > 3 and t.endswith("s"):
        return t[:-1]
    return t


def _sha_content(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def _ollama_chat(
    host: str, port: int, model: str, temperature: float, prompt: str
) -> Optional[dict]:
    try:
        parsed_host = host.replace("http://", "").replace("https://", "")
        if ":" in parsed_host:
            parsed_host = parsed_host.split(":")[0]
        conn = http.client.HTTPConnection(parsed_host, port=port, timeout=30)
        payload = json.dumps(
            {
                "model": model,
                "prompt": prompt,
                "stream": False,
                "format": "json",
                "options": {"temperature": temperature},
            }
        )
        headers = {"Content-Type": "application/json"}
        conn.request("POST", "/api/generate", payload, headers)
        res = conn.getresponse()
        data = res.read()
        conn.close()
        raw = data.decode("utf-8")
        j = json.loads(raw)
        if "response" in j:
            txt = j.get("response") or ""
            try:
                return json.loads(txt)
            except Exception:
                m = re.search(
                    r"\\{\\s*\\\"items\\\"\\s*:\\s*\\[.*?\\]\\s*\\}",
                    txt,
                    flags=re.DOTALL,
                )
                if m:
                    try:
                        return json.loads(m.group(0))
                    except Exception:
                        return None
        return None
    except Exception:
        return None


def _build_prompt(field_type: str, content: str, cfg: dict) -> str:
    if field_type == "tag":
        return (
            "Given the user's note content, extract 3-10 tags. The tags should be concepts and should be related to what the note is about. It should not be random items in the note. "
            'Do not include duplicates. Output JSON with array \'items\', each item {"value": string, "confidence": number between 0 and 1}. '
            'If there are any entities mentioned in the note, suggest tags for them. For example, if the note mentions "Never Eat Alone", suggest "never-eat-alone". The output should always be in kebab-case.'
            "Content:\n" + content
        )
    if field_type == "source":
        return (
            "From the user's note content, infer sources. If content say 'James told me', suggest 'james'; always kebab-case the person/entity. "
            "If content is reflection by the user referencing a book like 'Never Eat Alone', include both 'me' (as the user is generating the reflection) and 'never-eat-alone'. "
            'Normalize all sources to kebab-case. Output JSON with array \'items\', each item {"value": string, "confidence": number between 0 and 1}. '
            "Content:\n" + content
        )
    if field_type == "alias":
        return (
            "Based on the following note content, generate 3-5 meaningful and concise aliases or titles. "
            "These aliases should capture the main topic or essence of the note. "
            'Output JSON with array \'items\', each item {"value": string, "confidence": number between 0 and 1}. '
            "Make sure aliases are clear, descriptive, and under 50 characters. "
            "Content:\n" + content
        )
    return ""


@app.get("/api/config")
def api_config():
    cfg = normalize_config(load_config(_config_path))
    return cfg


def _ollama_health(host: str, port: int) -> bool:
    try:
        parsed_host = host.replace("http://", "").replace("https://", "")
        if ":" in parsed_host:
            parsed_host = parsed_host.split(":")[0]
        conn = http.client.HTTPConnection(parsed_host, port=port, timeout=3)
        conn.request("GET", "/api/version")
        res = conn.getresponse()
        ok = res.status == 200
        conn.close()
        return ok
    except Exception:
        return False


@app.get("/api/clipboard")
def api_clipboard():
    """Get current clipboard content."""
    try:
        result = subprocess.run(
            ["wl-paste", "-t", "text"], capture_output=True, text=True, timeout=2
        )
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
        cfg = normalize_config(load_config(_config_path))
        media_dir = Path(cfg["vault"]["path"]).expanduser() / cfg["vault"]["media_dir"]
        media_dir.mkdir(parents=True, exist_ok=True)
        screenshot_path = media_dir / f"{timestamp}_screenshot.png"

        # grimblast --notify  --freeze save area - > {screenshot path}
        import os

        result = os.system(
            f"grimblast --notify --freeze save area - > {screenshot_path}"
        )
        # result = subprocess.run(
        #     [
        #         "grimblast",
        #         "--notify",
        #         "--freeze",
        #         "save",
        #         "-",
        #         ">",
        #         str(screenshot_path),
        #     ],
        #     capture_output=True,
        #     timeout=50,
        # )

        if result == 0:
            return {"path": str(screenshot_path), "success": True}
        return {"success": False, "error": "Screenshot failed"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def _validate_modalities_have_content(capture_data, modalities):
    """Validate that selected modalities have actual content."""
    if not modalities:
        return False

    for modality in modalities:
        if modality == "text":
            content = capture_data.get("content", "").strip()
            if not content:
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

    return True


@app.post("/api/capture")
async def api_capture(
    content: str = Form(""),
    context: str = Form(""),
    tags: str = Form(""),
    sources: str = Form(""),
    alias: str = Form(""),
    capture_id: str = Form(""),
    modalities: str = Form(""),
    clipboard: str = Form(""),
    screenshot_path: str = Form(""),
    screenshot_type: str = Form(""),
    created_date: Optional[str] = Form(None),
    last_edited_date: Optional[str] = Form(None),
    media: Optional[List[UploadFile]] = File(None),
):
    cfg = normalize_config(load_config(_config_path))
    writer = SafeMarkdownWriter(str(Path(cfg["vault"]["path"]).expanduser()))
    ts = datetime.now(timezone.utc)
    cds = created_date or ts.date().isoformat()
    les = last_edited_date or ts.date().isoformat()
    tag_list = (
        [t.strip() for t in tags.split(",") if t.strip()]
        if isinstance(tags, str)
        else []
    )
    src_list = (
        [s.strip() for s in sources.split(",") if s.strip()]
        if isinstance(sources, str)
        else []
    )
    mod_list = (
        [m.strip() for m in modalities.split(",") if m.strip()]
        if isinstance(modalities, str)
        else []
    )
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

    # Use provided capture_id if available, otherwise generate a new one using timestamp
    actual_capture_id = capture_id.strip() if capture_id.strip() else ts.isoformat()
    
    # Handle alias - if provided, add it to the aliases list
    aliases = []
    if alias.strip():
        aliases.append(alias.strip())
    
    # Initialize capture data
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
        "capture_id": actual_capture_id,
        "aliases": aliases
    }

    if not _validate_modalities_have_content(capture, mod_list):
        return JSONResponse(
            {"error": "No content provided for selected modalities"}, status_code=400
        )

    p = writer.write_capture(capture)

    get_main_db().store_capture_data(capture)

    import os

    file_exists = os.path.exists(p) if p else False

    try:
        # Store the last used tags and sources in the database for persistence
        # Distinguish between AI-suggested and user-added tags/sources
        global _ai_suggested_tags, _ai_suggested_sources

        # Find which tags were AI-suggested vs user-added
        user_tags = [tag for tag in tag_list if tag not in _ai_suggested_tags]
        user_sources = [
            source for source in src_list if source not in _ai_suggested_sources
        ]

        # Store both sets separately
        get_main_db().store_last_used_values(
            {"tags": user_tags, "sources": user_sources},
            {
                "tags": [
                    tag for tag in tag_list if tag in _ai_suggested_tags
                ],  # Only keep AI tags that were actually used
                "sources": [
                    source for source in src_list if source in _ai_suggested_sources
                ],  # Only keep AI sources that were actually used
            },
        )

        # Return a properly formatted JSON response
        return {"saved_to": str(p), "verified": file_exists}
    except Exception as e:
        # Return a properly formatted JSON error response
        return JSONResponse({"error": f"Save failed: {str(e)}"}, status_code=500)


@app.get("/api/suggestions/{field_type}")
def api_suggestions(field_type: str, query: str = "", limit: int = 10):
    if field_type not in ["tag", "source", "context"]:
        return JSONResponse({"error": "Invalid field type"}, status_code=400)
    suggestions = get_main_db().get_suggestions(field_type, query, limit)
    return {
        "suggestions": [
            {
                "value": s.value,
                "count": s.count,
                "last_used": s.last_used.isoformat(),
                "color": s.color,
            }
            for s in suggestions
        ]
    }


@app.get("/api/suggestion-exists/{field_type}")
def api_suggestion_exists(field_type: str, value: str):
    """Check if a suggestion value exists in the database."""
    if field_type not in ["tag", "source", "context"]:
        return JSONResponse({"error": "Invalid field type"}, status_code=400)

    exists = get_main_db().suggestion_exists(value, field_type)
    return {"exists": exists}


@app.post("/api/ai-suggestions/feedback")
async def api_ai_suggestions_feedback(
    field_type: str = Form(...),
    value: str = Form(...),
    action: str = Form(...),
    confidence: Optional[float] = Form(None),
    edited_value: Optional[str] = Form(None),
    content_hash: Optional[str] = Form(None),
):
    if field_type not in ["tag", "source", "context"]:
        return JSONResponse({"error": "Invalid field type"}, status_code=400)
    get_main_db().store_suggestion_feedback(
        field_type, value, action, confidence, edited_value, content_hash
    )
    return {"ok": True}


@app.get("/api/recent-values")
def api_recent_values():
    """Get the most recent values for field restoration."""
    recent_values = get_main_db().get_most_recent_values()
    return {"recent_values": recent_values}


@app.post("/api/audio/start")
def api_audio_start(recorder_type: str = Form(...), recorder_id: str = Form(...)):
    """Start audio recording."""
    if not AUDIO_RECORDING_AVAILABLE or not audio_manager:
        return JSONResponse({"error": "Audio recording is not available"}, status_code=503)
    
    if not audio_manager.create_recorder(recorder_type, recorder_id):
        if recorder_id in audio_manager.recorders:
            return JSONResponse({"error": "Recorder already exists"}, status_code=400)
        return JSONResponse({"error": "Invalid recorder type"}, status_code=400)

    if not audio_manager.start_recording(recorder_id):
        return JSONResponse({"error": "Failed to start recording"}, status_code=500)

    return {"status": "recording_started", "recorder_id": recorder_id}


@app.post("/api/audio/stop")
def api_audio_stop(recorder_id: str = Form(...)):
    """Stop audio recording and save file."""
    if not AUDIO_RECORDING_AVAILABLE or not audio_manager:
        return JSONResponse({"error": "Audio recording is not available"}, status_code=503)
    
    if not audio_manager.stop_recording(recorder_id):
        return JSONResponse({"error": "Failed to stop recording"}, status_code=500)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
    filename = f"audio_{recorder_id}_{timestamp}.wav"
    cfg = normalize_config(load_config(_config_path))
    filepath = (
        Path(cfg["vault"]["path"]).expanduser() / cfg["vault"]["media_dir"] / filename
    )
    filepath.parent.mkdir(parents=True, exist_ok=True)

    if not audio_manager.save_recording(recorder_id, filepath):
        return JSONResponse({"error": "Failed to save recording"}, status_code=500)

    audio_manager.cleanup_recorder(recorder_id)

    return {
        "status": "recording_saved",
        "filename": filename,
        "filepath": str(filepath),
    }


@app.get("/api/ai-suggestions/{field_type}")
def api_ai_suggestions(field_type: str, content: str = "", limit: int = 10):
    print(f"Getting AI suggestions for {field_type} with content length {len(content)}")
    if field_type not in ["tag", "source", "alias"]:
        return JSONResponse({"error": "Invalid field type"}, status_code=400)
    
    # Special handling for alias suggestions
    if field_type == "alias":
        content_norm = (content or "").strip()
        if not content_norm:
            return {"ai": [], "content_hash": None}
        h = _sha_content(content_norm)
        
        # First try to use the Ollama LLM directly
        cfg = normalize_config(load_config(_config_path))
        ai_mode = (cfg.get("ai") or {}).get("mode") or "local"
        ai_cfg = (cfg.get("ai") or {}).get("ollama") or {}
        
        # Get Ollama server config
        host = ai_cfg.get("host") or "http://127.0.0.1"
        port = int(ai_cfg.get("port") or 11434)
        model = ai_cfg.get("model") or "llama3.2:3b"
        temperature = float((cfg.get("ai") or {}).get("ollama", {}).get("temperature", 0.2) or 0.2)
        
        # Build specialized prompt for aliases
        prompt = (
            "Based on the following note content, generate {limit} meaningful and concise aliases or titles. "
            "These aliases should capture the main topic or essence of the note. "
            "Output JSON with array 'items', each item {{\"value\": string, \"confidence\": number between 0 and 1}}. "
            "Make sure aliases are clear, descriptive, and under 50 characters. "
            "Content:\n{content}"
        ).format(limit=limit, content=content_norm[:1000] if len(content_norm) > 1000 else content_norm)
        
        try:
            # Try to use Ollama directly
            ai_resp = _ollama_chat(host, port, model, temperature, prompt)
            if ai_resp and "items" in ai_resp and isinstance(ai_resp["items"], list):
                return {"ai": ai_resp["items"][:limit], "content_hash": h}
        except Exception as e:
            print(f"Ollama alias generation error: {e}")
            
        # Fall back to the module if available or basic suggestions
        if ALIAS_SUGGESTIONS_AVAILABLE:
            suggestions = generate_aliases(content_norm, limit)
            return {"ai": suggestions, "content_hash": h}
        else:
            # Basic fallback if module not available
            return {"ai": [{"value": f"Note from {datetime.now().strftime('%Y-%m-%d')}", "confidence": 0.5}], "content_hash": h}
    
    # For tags and sources, continue with regular LLM-based suggestions
    cfg = normalize_config(load_config(_config_path))
    content_norm = (content or "").strip()
    if not content_norm:
        return {"ai": [], "content_hash": None}
    h = _sha_content(content_norm)
    k = f"{field_type}:{h}"
    ai_mode = (cfg.get("ai") or {}).get("mode") or "local"
    ai_cfg = (cfg.get("ai") or {}).get("ollama") or {}
    temperature = float(
        (cfg.get("ai") or {}).get("ollama", {}).get("temperature", 0) or 0
    )
    suggest_existing_only = bool(
        (cfg.get("ai") or {}).get("behavior", {}).get("suggest_existing_only", False)
    )
    include_db_boost = bool(
        (cfg.get("ai") or {}).get("behavior", {}).get("include_db_priority_boost", True)
    )
    if k in _ai_cache:
        ai_items = _ai_cache[k]
    else:
        prompt = _build_prompt(field_type, content_norm, cfg)
        ai_resp = None
        if ai_mode in ["local", "hybrid"]:
            host = ai_cfg.get("host") or "http://127.0.0.1"
            port = int(ai_cfg.get("port") or 11434)
            model = ai_cfg.get("model") or "llama3.2:3b"
            ai_resp = _ollama_chat(host, port, model, temperature, prompt)
        items = []
        if isinstance(ai_resp, dict) and isinstance(ai_resp.get("items"), list):
            for it in ai_resp["items"]:
                v = str(it.get("value", "")).strip()
                if not v:
                    continue
                c = float(it.get("confidence", 0.5))
                if field_type == "tag" and (cfg.get("ai") or {}).get(
                    "normalization", {}
                ).get("tags_kebab", True):
                    v = _kebab_case(v)
                if field_type == "source" and (cfg.get("ai") or {}).get(
                    "normalization", {}
                ).get("sources_kebab", True):
                    v = _kebab_case(v)
                items.append({"value": v, "confidence": c})
        _ai_cache[k] = items
        ai_items = items
    if suggest_existing_only:
        base = get_main_db().get_suggestions(field_type, "", 500)
        db_set = set([s.value for s in base])
        ai_items = [x for x in ai_items if x["value"] in db_set]
    if include_db_boost:
        boosted = []
        for x in ai_items:
            b = 0.2 if get_main_db().suggestion_exists(x["value"], field_type) else 0.0
            boosted.append(
                {
                    "value": x["value"],
                    "confidence": min(1.0, max(0.0, x["confidence"] + b)),
                }
            )
        ai_items = boosted
    original_items = ai_items
    ai_items = sorted(ai_items, key=lambda x: x.get("confidence", 0), reverse=True)[
        :limit
    ]
    if original_items != ai_items:
        for fi in ai_items:
            print(f"Boosted: {fi['value']}, {fi['confidence']}")

    # Track AI suggested items
    global _ai_suggested_tags, _ai_suggested_sources
    ai_values = [item["value"] for item in ai_items]

    if field_type == "tag":
        _ai_suggested_tags = set(ai_values)
    elif field_type == "source":
        _ai_suggested_sources = set(ai_values)
    # For aliases, we don't need to track them globally, as they are specific to each note

    return {"ai": ai_items, "content_hash": h}


@app.get("/api/audio/status/{recorder_id}")
def api_audio_status(recorder_id: str):
    """Get audio recording status."""
    status = audio_manager.get_recording_status(recorder_id)
    return status


@app.websocket("/ws/audio-waveform/{recorder_id}")
async def websocket_audio_waveform(websocket: WebSocket, recorder_id: str):
    """WebSocket endpoint for real-time waveform data."""
    await websocket.accept()
    
    if not AUDIO_RECORDING_AVAILABLE or not audio_manager:
        await websocket.send_json({"error": "Audio recording is not available"})
        await websocket.close()
        return
    
    audio_manager.add_websocket_connection(recorder_id, websocket)

    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        audio_manager.remove_websocket_connection(recorder_id, websocket)


@app.get("/capture/raw_capture/media/{filename}")
def serve_media_file(filename: str):
    """Serve media files from the vault's media directory."""
    cfg = normalize_config(load_config(_config_path))
    media_path = Path(cfg["vault"]["path"]).expanduser() / cfg["vault"]["media_dir"] / filename
    
    if not media_path.exists():
        return JSONResponse({"error": "File not found"}, status_code=404)
    
    if not media_path.is_file():
        return JSONResponse({"error": "Not a file"}, status_code=400)
    
    # Serve the file
    return FileResponse(media_path)


@app.get("/api/ai/health")
def api_ai_health():
    cfg = normalize_config(load_config(_config_path))
    ai_cfg = cfg.get("ai") or {}
    mode = ai_cfg.get("mode") or "local"
    provider = ai_cfg.get("provider") or "ollama"
    connected = False
    details = {}
    if provider == "ollama" and mode in ["local", "hybrid"]:
        o = ai_cfg.get("ollama") or {}
        host = o.get("host") or "http://127.0.0.1"
        port = int(o.get("port") or 11434)
        connected = _ollama_health(host, port)
        details = {"host": host, "port": port, "model": o.get("model") or "llama3.2:3b"}
    return {
        "provider": provider,
        "mode": mode,
        "connected": bool(connected),
        "details": details,
    }


if web_dist_path.exists():
    app.mount("/", StaticFiles(directory=str(web_dist_path), html=True), name="static")
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Knowledge Management System Server")
    parser.add_argument("--config", type=str, help="Path to config file")
    args = parser.parse_args()

    _config_path = args.config

    cfg = normalize_config(load_config(_config_path))

    db_path = cfg["database"]["path"]
    db_dir = Path(db_path).parent
    db_dir.mkdir(parents=True, exist_ok=True)

    main_db = MainDatabase(db_path)

    if cfg.get("is_dev"):
        print("🚧 RUNNING IN DEVELOPMENT MODE 🚧")

    config = Config()
    config.bind = [f"0.0.0.0:{int(os.environ.get('PORT', '7123'))}"]
    config.use_reloader = False
    config.accesslog = "-"

    asyncio.run(serve(app, config))

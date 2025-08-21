import json
import threading
from typing import List, Dict, Any, Tuple
from urllib import request
from urllib.error import URLError
from urllib.parse import urljoin
from hashlib import sha256


class _Inflight:
    def __init__(self):
        self.event = threading.Event()
        self.result: List[Dict[str, Any]] = []
        self.error: Exception | None = None


class AISuggester:
    def __init__(self, ai_cfg: Dict[str, Any]):
        self.endpoint = ai_cfg.get("endpoint", "http://127.0.0.1:11434")
        self.model = ai_cfg.get("model", "llama-3.2-3b")
        self.temperature = float(ai_cfg.get("temperature", 0))
        self.timeout = 12
        self.lock = threading.Lock()
        self.inflight: Dict[Tuple[str, str], _Inflight] = {}

    def _prompt_for(self, field_type: str, content: str) -> str:
        if field_type == "tag":
            return (
                "You are to extract up to 8 concise tags from the provided note "
                "content. Use singular nouns where applicable. Output strictly as "
                "JSON array of objects with keys 'value' and 'confidence' (0..1). "
                "Values should be kebab-case."
                "\nContent:\n" + content
            )
        else:
            return (
                "You are to extract up to 8 likely sources referenced in the note "
                "content. Sources can be people, books, or organizations. Output "
                "strictly as JSON array of objects with keys 'value' and 'confidence' "
                "(0..1). Values must be kebab-case."
                "\nContent:\n" + content
            )

    def _call_ollama(self, prompt: str) -> str:
        url = urljoin(self.endpoint.rstrip("/") + "/", "api/generate")
        data = json.dumps(
            {
                "model": self.model,
                "prompt": prompt,
                "options": {"temperature": self.temperature},
            }
        ).encode("utf-8")
        req = request.Request(
            url, data=data, headers={"Content-Type": "application/json"}
        )
        with request.urlopen(req, timeout=self.timeout) as resp:
            raw = resp.read().decode("utf-8")
            try:
                obj = json.loads(raw)
                return obj.get("response", "")
            except Exception:
                return raw

    def _extract_json(self, text: str) -> List[Dict[str, Any]]:
        try:
            text = text.strip()
            start = text.find("[")
            end = text.rfind("]")
            if start != -1 and end != -1 and end > start:
                arr = json.loads(text[slice(start, end + 1)])
                if isinstance(arr, list):
                    out = []
                    for it in arr:
                        if not isinstance(it, dict):
                            continue
                        v = str(it.get("value", "")).strip()
                        try:
                            c = float(it.get("confidence", 0))
                        except Exception:
                            c = 0.0
                        if v:
                            out.append(
                                {"value": v, "confidence": max(0.0, min(1.0, c))}
                            )
                    return out
        except Exception:
            return []
        return []

    def generate(self, field_type: str, content: str) -> List[Dict[str, Any]]:
        content_hash = sha256(content.encode("utf-8")).hexdigest()
        key = (field_type, content_hash)
        with self.lock:
            if key in self.inflight:
                infl = self.inflight[key]
                waiter = infl
            else:
                infl = _Inflight()
                self.inflight[key] = infl
                waiter = None
        if waiter is not None:
            waiter.event.wait(timeout=self.timeout + 2)
            return waiter.result

        try:
            prompt = self._prompt_for(field_type, content)
            try:
                raw = self._call_ollama(prompt)
            except URLError:
                raw = "[]"
            items = self._extract_json(raw)
            infl.result = items
            return items
        finally:
            infl.event.set()
            with self.lock:
                self.inflight.pop(key, None)

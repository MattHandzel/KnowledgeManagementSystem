Profiling scripts

- profile_baseline.py: run against the Python FastAPI backend on http://localhost:7123
  - Measures p50/p95/avg for /api/config, /api/clipboard, /api/screenshot, and /api/capture
  - Usage:
    - Start server: source .venv/bin/activate && python server/app.py
    - Run: python scripts/profile_baseline.py

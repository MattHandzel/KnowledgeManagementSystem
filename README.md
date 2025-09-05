Knowledge Management System

React Web App (new)
A React web app with a Python FastAPI backend that produce markdown files in your configured vault.

What’s included

- React (Vite + TypeScript) app in web/
- FastAPI backend in server/app.py
- Functional parity:
  - Fields: content, context, tags, sources
  - Modalities: text, clipboard (live preview), screenshot, audio, files
  - Keybindings: Ctrl+S save, ESC cancel, Tab/Shift+Tab navigation, F1 help toggle
  - Clipboard preview: polls navigator.clipboard.readText at interval from ui.clipboard_poll_ms (config.yaml)
  - Screenshot: uses getDisplayMedia to capture a screen/window and attaches the image to the capture
  - Save: writes Markdown with frontmatter (ISO8601 UTC +00:00 timestamps with no microseconds, id, aliases, created_date, last_edited_date; importance null; no extra blank line after frontmatter)

Run locally
Backend

- Install dependencies:
  - python3 -m venv .venv && source .venv/bin/activate
  - pip install -r server/requirements.txt
- Start the server:
  - python server/app.py
  - By default it serves at http://localhost:7123
- The server reads config.yaml to determine vault.path, capture_dir, media_dir.

Frontend

- From web/:
  - npm install (or pnpm i / yarn)
  - npm run dev
  - Visit http://localhost:5173 (the app calls /api on localhost:7123)
- Keyboard:
  - Ctrl+S saves
  - Ctrl+1..9 toggles modalities (plain numbers just type into fields)
  - F1 toggles help
  - ESC clears the form

Saving behavior

- Files are saved under: {vault.path}/{vault.capture_dir}
- Media files are saved under: {vault.path}/{vault.media_dir}
- Frontmatter conforms to:
  - timestamp: ISO8601 UTC (e.g. 2025-08-16T06:58:42+00:00)
  - id: same as capture_id
  - aliases: [capture_id]
  - created_date, last_edited_date: YYYY-MM-DD
  - importance: null
  - sources: array of strings
  - No extra newline between closing --- and ## Content

Notes

- Clipboard preview requires clipboard permission in the browser. If the preview is empty, click the page and try again.
- Screenshot capture uses browser APIs; depending on the browser, a picker is shown to choose the screen/window to capture.

## Electron Desktop App

The Knowledge Management System is available as an Electron desktop application that combines the React frontend with the FastAPI backend in a single package.

### Development Setup

```bash
# Clone and enter directory
cd KnowledgeManagementSystem

# Enter development shell (requires Nix)
nix develop

# Start backend server
cd server && python app.py

# Start frontend (in another terminal)
cd web && npm run dev

# Launch Electron app (in another terminal)
cd electron && npm install && npm start
```

### Building Package

```bash
# Build with nix
nix build

# Install to system
nix profile install .

# Run installed app
kms-electron
```

## Configuration

Edit `config.yaml` to customize:

```yaml
vault:
  path: "~/notes"
  capture_dir: "capture/raw_capture"
  media_dir: "capture/raw_capture/media"

ui:
  clipboard_poll_ms: 200

capture:
  auto_detect_modalities: true
  context_suggestions: true
  tag_suggestions: true
```

## Development

### Testing

```bash
# Run tests
pytest tests/

# Format code
black *.py

# Lint code
flake8 *.py

# Type checking
mypy *.py
```

## License

MIT License - see LICENSE file for details.

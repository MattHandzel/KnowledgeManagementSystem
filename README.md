Knowledge Management System (Terminal + Web)

React Web App (new)
A new React web app provides the same capture functionality as the terminal UI, with a small Python FastAPI backend that reuses the existing SafeMarkdownWriter to produce markdown files in your configured vault.

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
  - By default it serves at http://localhost:5174
- The server reads config.yaml to determine vault.path, capture_dir, media_dir.

Frontend
- From web/:
  - npm install (or pnpm i / yarn)
  - npm run dev
  - Visit http://localhost:5173 (the app calls /api on localhost:5174)
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
- The terminal app remains unchanged and continues to work as before.
# Terminal Capture Daemon

Ultra-lightweight, keyboard-driven knowledge capture system for NixOS and Hyprland. Provides instant popup capture interface with semantic keybindings and stores individual ideas as markdown files.

## Features

- **Instant Response**: Background daemon with Unix socket communication
- **Terminal UI**: ncurses-based interface with semantic keybindings
- **Individual Ideas**: Each capture stored as separate markdown file
- **Multimodal**: Text, clipboard, screenshot, audio, and file capture
- **File Safety**: Atomic operations with unique filename generation
- **Reversible**: Pure markdown with YAML frontmatter, Obsidian compatible
- **NixOS Ready**: Flake-based development and deployment

## Quick Start

### Development Setup

```bash
# Clone and enter directory
cd capture_daemon

# Enter development shell (requires Nix)
nix develop

# Test the markdown writer
python markdown_writer.py

# Start daemon
python capture_daemon.py --daemon

# Test trigger (in another terminal)
python trigger_capture.py quick
```

### Hyprland Integration

Add to your `~/.config/hypr/hyprland.conf`:

```conf
# Capture keybinds
bind = SUPER, C, exec, python /path/to/capture_daemon/trigger_capture.py quick
bind = SUPER SHIFT, C, exec, python /path/to/capture_daemon/trigger_capture.py multimodal
bind = SUPER ALT, C, exec, python /path/to/capture_daemon/trigger_capture.py voice
bind = SUPER CTRL, C, exec, python /path/to/capture_daemon/trigger_capture.py screenshot

# Window rules for capture popup
windowrulev2 = float,class:^(capture-daemon)$
windowrulev2 = size 800 600,class:^(capture-daemon)$
windowrulev2 = center,class:^(capture-daemon)$
windowrulev2 = animation slide,class:^(capture-daemon)$

# Auto-start daemon
exec-once = python /path/to/capture_daemon/capture_daemon.py --daemon
```

## Architecture

- **Background Daemon**: Long-running process with ncurses UI
- **Trigger Script**: Lightweight script called by Hyprland keybinds  
- **Markdown Writer**: Safe file operations with unique ID generation
- **Individual Storage**: Each idea gets its own markdown file
- **Media Handling**: Files stored in `~/notes/capture/raw_capture/media/`

## File Structure

```
~/notes/capture/raw_capture/
├── 20240815_213245_123.md     # Individual idea files
├── 20240815_213301_456.md
├── 20240815_213445_789.md
└── media/                     # Media attachments
    ├── 20240815_213245_screenshot.png
    └── 20240815_213301_audio.wav
```

## Keybindings

### Global Actions
- `Ctrl+S`: Save capture and exit
- `ESC`: Cancel without saving
- `Tab` / `Shift+Tab`: Navigate fields
- `F1`: Toggle help

### Content Field
- `↑↓←→` or `hjkl`: Navigate cursor
- `Home/End` or `Ctrl+A/E`: Line boundaries
- `Page Up/Down`: Scroll content
- `Ctrl+U`: Clear line
- `Ctrl+W`: Delete word

### Context & Tags Fields
- `←→`: Navigate cursor
- `Home/End`: Field boundaries
- `Ctrl+U`: Clear field
- `Enter`: Next field

### Modalities
- `←→`: Navigate options
- `Space/Enter`: Toggle modality
- `1-5`: Toggle by number

## Configuration

Edit `config.yaml` to customize:

```yaml
vault:
  path: "~/notes"
  capture_dir: "capture/raw_capture"
  media_dir: "capture/raw_capture/media"

daemon:
  socket_path: "/tmp/capture_daemon.sock"
  auto_start: true

ui:
  theme: "default"
  window_size: [80, 24]
  auto_focus_content: true

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

### Building Package

```bash
# Build with nix
nix build

# Install to system
nix profile install .
```

## Troubleshooting

### Daemon Won't Start
- Check socket permissions: `ls -la /tmp/capture_daemon.sock`
- Verify directories exist: `ls -la ~/notes/capture/raw_capture/`
- Check logs: `python capture_daemon.py --daemon` (foreground mode)

### Capture UI Issues
- Ensure terminal supports ncurses: `echo $TERM`
- Check Python dependencies: `python -c "import curses, yaml"`
- Test direct UI: `python capture_daemon.py --mode quick`

### Media Capture Fails
- Verify tools installed: `which grim slurp wl-paste arecord`
- Check Wayland session: `echo $WAYLAND_DISPLAY`
- Test tools manually: `grim test.png`

## License

MIT License - see LICENSE file for details.

# Terminal Capture Daemon

Ultra-lightweight, keyboard-driven knowledge capture system for NixOS and Hyprland. Provides instant popup capture interface with semantic keybindings and stores individual ideas as markdown files.

## Web App

A browser-based, terminal-style UI is available under `client/` that mimics the ncurses interface and keybindings. It runs locally, behaves like a desktop capture app, and saves captures by downloading a `.md` file that matches the daemon’s YAML + Markdown format.

- Read-through: See docs/REPO_READTHROUGH.md
- Local dev:
  - cd client
  - npm install
  - npm run dev
- Build:
  - npm run build
### Desktop App (Electron)
- Nix shell: in repo root, run:
  - nix develop
- Dev run (Electron + Vite):
  - cd client
  - npm ci
  - npm run app:dev
- Package (Linux AppImage):
  - cd client
  - npm run electron:build
  - The artifact will be created under the client/dist directory (electron-builder output)
  - npm run preview

### Keybindings (client)
- Ctrl+S: Save and download .md
- ESC: Clear all fields
- Tab / Shift+Tab: Switch field
- F1: Toggle help
- Ctrl+B: Browse mode
- Ctrl+E: Edit selected idea from browse
- 1–5: Toggle modalities (1=text 2=clipboard 3=screenshot 4=audio 5=files)
- j/k: Navigate the idea list in browse mode

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
├── 20240815_213245_123.md
├── 20240815_213301_456.md
├── 20240815_213445_789.md
└── media/
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

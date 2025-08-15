# Terminal-Based Knowledge Capture Daemon - Design Specification

## Overview

A lightweight, terminal-based knowledge capture system for NixOS + Hyprland that provides instant popup capture interface with semantic keybindings. The system stores captures as markdown files with YAML frontmatter in the user's existing vault structure at `~/notes/capture/raw_capture`.

## Architecture

### System Components

```
Hyprland Keybind → trigger_capture.py → Unix Socket → capture_daemon.py → ncurses UI → markdown file
```

1. **Background Daemon** (`capture_daemon.py`): Long-running process with ncurses UI
2. **Trigger Script** (`trigger_capture.py`): Lightweight script called by Hyprland keybinds
3. **Markdown Writer** (`markdown_writer.py`): Safe file operations with conflict resolution
4. **Configuration** (`config.yaml`): User preferences and paths
5. **Installation** (`install.sh`): Setup script for NixOS

### File Structure

```
~/capture_daemon/
├── DESIGN_SPECIFICATION.md    # This document
├── capture_daemon.py           # Main daemon with ncurses UI
├── trigger_capture.py          # Keybind trigger script
├── markdown_writer.py          # Safe file operations
├── keybindings.py             # Semantic keybinding handler
├── config.yaml                # Configuration
├── install.sh                 # NixOS setup script
├── shell.nix                  # Development environment
└── README.md                  # Usage instructions
```

### Vault Integration

**Target Directory**: `~/notes/capture/raw_capture/`
**File Format**: Individual markdown files per idea with YAML frontmatter
**Naming Convention**: `YYYYMMDD_HHMMSS_microseconds.md` (e.g., `20240815_213245_123.md`)
**Media Storage**: `~/notes/capture/raw_capture/media/` for attachments

## User Interface Design

### Terminal UI Layout (ncurses)

```
┌─ Quick Capture ─────────────────────────────────────────────────────┐
│ Mode: [TEXT] [CLIPBOARD] [SCREENSHOT] [AUDIO] [FILES]               │
├─────────────────────────────────────────────────────────────────────┤
│ Content:                                                            │
│ ┌─────────────────────────────────────────────────────────────────┐ │
│ │ Type your capture here...                                       │ │
│ │                                                                 │ │
│ │ [Cursor here in insert mode]                                    │ │
│ │                                                                 │ │
│ └─────────────────────────────────────────────────────────────────┘ │
├─────────────────────────────────────────────────────────────────────┤
│ Context: reading research paper                                     │
│ Tags: research, ml, attention                                       │
├─────────────────────────────────────────────────────────────────────┤
│ Ctrl+S Save  ESC Cancel  Tab Next Field  ↑↓←→ Navigate             │
└─────────────────────────────────────────────────────────────────────┘
```

### Semantic Keybindings

**Navigation & Editing**:
- `↑↓←→` or `hjkl`: Navigate cursor/fields
- `Tab` / `Shift+Tab`: Next/previous field
- `Home` / `End`: Beginning/end of line
- `Ctrl+A` / `Ctrl+E`: Beginning/end of line (alternative)
- `Page Up` / `Page Down`: Scroll content area

**Actions**:
- `Ctrl+S`: Save capture and close
- `ESC`: Cancel capture without saving
- `Enter`: New line in content area, confirm in other fields
- `Backspace` / `Delete`: Delete characters
- `Ctrl+U`: Clear current line
- `Ctrl+W`: Delete previous word

**Modes**:
- `Space`: Toggle capture mode (text/clipboard/screenshot/audio)
- `Ctrl+M`: Toggle multimodal capture
- `F1`: Show help overlay

**Field-Specific**:
- In content area: Normal text editing
- In context field: Auto-complete from previous captures
- In tags field: Comma-separated tags with auto-complete

## Data Models

### Capture Entry Structure

```yaml
---
timestamp: "2024-08-15 21:32:45.123 UTC"
capture_id: "20240815_213245_123"
modalities: ["text", "clipboard"]
context:
  activity: "reading research paper"
  location: "home_office"
  device: "laptop"
  wifi_network: "home_network"
metadata:
  weather: null
  previous_context: "studying machine learning"
  auto_populated: true
processing_status: "raw"
importance: 0.5
tags: ["research", "ml", "attention"]
---

# Quick note about transformer attention mechanisms

## Content
Quick note about transformer attention mechanisms - the key insight is that attention allows the model to focus on relevant parts of the input sequence.

## Clipboard
```python
def attention(Q, K, V):
    return softmax(Q @ K.T / sqrt(d_k)) @ V
```

## Media
- Screenshot: ![Screenshot](media/20240815_213245_screenshot.png)
```

### Configuration Schema

```yaml
# config.yaml
vault:
  path: "~/notes"
  capture_dir: "capture/raw_capture"
  media_dir: "capture/media"
  
daemon:
  socket_path: "/tmp/capture_daemon.sock"
  auto_start: true
  hot_reload: true
  
ui:
  theme: "default"
  window_size: [80, 24]
  auto_focus_content: true
  
capture:
  auto_detect_modalities: true
  context_suggestions: true
  tag_suggestions: true
  default_importance: 0.5
  
development:
  debug_logging: false
  test_mode: false
```

## File Safety Mechanisms

### Conflict Resolution Strategy

1. **Daily File Existence Check**:
   - Check if `YYYY-MM-DD.md` exists
   - If exists, append to file with timestamp separator
   - Never overwrite existing content

2. **Atomic Write Operations**:
   - Write to temporary file first
   - Verify write success
   - Atomic move to final location
   - Rollback on failure

3. **Backup Strategy**:
   - Create `.backup` copy before any modification
   - Keep last 5 backups per daily file
   - Auto-cleanup old backups after 30 days

4. **Media File Handling**:
   - Generate unique filenames with timestamp + random suffix
   - Check for existing files before writing
   - Use content hash for duplicate detection

### Implementation Details

```python
class SafeMarkdownWriter:
    def __init__(self, vault_path):
        self.vault_path = Path(vault_path).expanduser()
        self.capture_dir = self.vault_path / "capture" / "raw_capture"
        self.media_dir = self.vault_path / "capture" / "raw_capture" / "media"
        
    def write_capture(self, capture_data):
        idea_file = self.get_idea_file(capture_data.get('timestamp'), capture_data.get('capture_id'))
        
        # Ensure unique filename
        if idea_file.exists():
            idea_file = self.get_unique_idea_file(capture_data.get('timestamp'), capture_data.get('capture_id'))
        
        # Atomic write operation (new file)
        temp_file = idea_file.with_suffix('.tmp')
        try:
            with temp_file.open('w', encoding='utf-8') as f:
                f.write(self.format_capture(capture_data))
            temp_file.replace(idea_file)
        except Exception as e:
            temp_file.unlink(missing_ok=True)
            raise e
    
    def get_idea_file(self, timestamp, capture_id):
        if capture_id is None:
            capture_id = self.generate_capture_id(timestamp)
        filename = f"{capture_id}.md"
        return self.capture_dir / filename
```

## Multimodal Capture Implementation

### Supported Modalities

1. **Text**: Direct user input in content area
2. **Clipboard**: Current clipboard content (text/images)
3. **Screenshot**: Full screen or selection using `grim`
4. **Audio**: Voice recording using `arecord`
5. **Files**: File attachments via file picker

### Capture Workflow

```python
class MultimodalCapture:
    def __init__(self):
        self.active_modalities = set()
        
    def capture_clipboard(self):
        # Text clipboard
        text = subprocess.run(['wl-paste', '-t', 'text'], 
                            capture_output=True, text=True).stdout
        
        # Image clipboard  
        image_types = subprocess.run(['wl-paste', '-l'], 
                                   capture_output=True, text=True).stdout
        if 'image/' in image_types:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            image_path = self.media_dir / f"{timestamp}_clipboard.png"
            subprocess.run(['wl-paste', '-t', 'image/png'], 
                         stdout=image_path.open('wb'))
            return {"type": "image", "path": image_path}
        
        return {"type": "text", "content": text}
    
    def capture_screenshot(self, selection=False):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        screenshot_path = self.media_dir / f"{timestamp}_screenshot.png"
        
        cmd = ['grim']
        if selection:
            cmd.extend(['-g', '$(slurp)'])
        cmd.append(str(screenshot_path))
        
        subprocess.run(cmd)
        return {"type": "screenshot", "path": screenshot_path}
    
    def capture_audio(self, duration=None):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        audio_path = self.media_dir / f"{timestamp}_audio.wav"
        
        cmd = ['arecord', '-f', 'cd', str(audio_path)]
        # Implementation with duration handling and user control
        
        return {"type": "audio", "path": audio_path}
```

## NixOS Integration

### Development Environment

```nix
# shell.nix
{ pkgs ? import <nixpkgs> {} }:

pkgs.mkShell {
  buildInputs = with pkgs; [
    # Core dependencies
    python3
    python3Packages.pyyaml
    python3Packages.watchdog
    
    # Terminal UI
    ncurses
    
    # Capture tools
    grim          # Screenshots
    slurp         # Screen selection
    wl-clipboard  # Clipboard access
    wf-recorder   # Screen recording
    alsa-utils    # Audio recording (arecord)
    
    # Development tools
    python3Packages.pytest
    python3Packages.black
    python3Packages.flake8
  ];
  
  shellHook = ''
    echo "Terminal capture daemon development environment"
    echo "Usage:"
    echo "  python capture_daemon.py    # Start daemon"
    echo "  python trigger_capture.py   # Test trigger"
    echo "  pytest tests/               # Run tests"
    
    # Create required directories
    mkdir -p ~/notes/capture/raw_capture
    mkdir -p ~/notes/capture/media
    
    # Set up socket directory
    mkdir -p /tmp/capture_daemon
  '';
}
```

### System Integration

```bash
# install.sh - System setup script
#!/usr/bin/env bash

set -e

INSTALL_DIR="$HOME/.local/bin"
CONFIG_DIR="$HOME/.config/capture-daemon"
VAULT_DIR="$HOME/notes"

echo "Installing Terminal Capture Daemon..."

# Create directories
mkdir -p "$INSTALL_DIR"
mkdir -p "$CONFIG_DIR"
mkdir -p "$VAULT_DIR/capture/raw_capture"
mkdir -p "$VAULT_DIR/capture/media"

# Copy scripts
cp capture_daemon.py "$INSTALL_DIR/"
cp trigger_capture.py "$INSTALL_DIR/"
cp markdown_writer.py "$INSTALL_DIR/"
cp keybindings.py "$INSTALL_DIR/"

# Copy config
cp config.yaml "$CONFIG_DIR/"

# Make executable
chmod +x "$INSTALL_DIR/capture_daemon.py"
chmod +x "$INSTALL_DIR/trigger_capture.py"

# Add to PATH if not already there
if ! echo "$PATH" | grep -q "$INSTALL_DIR"; then
    echo "export PATH=\"$INSTALL_DIR:\$PATH\"" >> ~/.bashrc
fi

echo "Installation complete!"
echo "Add these keybinds to your Hyprland config:"
echo "bind = SUPER, C, exec, trigger_capture.py quick"
echo "bind = SUPER SHIFT, C, exec, trigger_capture.py multimodal"
```

### Hyprland Configuration

```conf
# ~/.config/hypr/hyprland.conf additions

# Capture daemon keybinds
bind = SUPER, C, exec, trigger_capture.py quick
bind = SUPER SHIFT, C, exec, trigger_capture.py multimodal  
bind = SUPER ALT, C, exec, trigger_capture.py voice
bind = SUPER CTRL, C, exec, trigger_capture.py screenshot

# Window rules for capture popup
windowrulev2 = float,class:^(capture-daemon)$
windowrulev2 = size 800 600,class:^(capture-daemon)$
windowrulev2 = center,class:^(capture-daemon)$
windowrulev2 = animation slide,class:^(capture-daemon)$

# Auto-start daemon
exec-once = capture_daemon.py --daemon
```

## Error Handling & Edge Cases

### Daemon Management

1. **Socket Conflicts**: Check for existing socket, clean up stale processes
2. **Permission Issues**: Graceful fallback to user-writable locations
3. **Process Recovery**: Auto-restart on crash, maintain capture queue
4. **Resource Limits**: Memory usage monitoring, cleanup old captures

### File System Edge Cases

1. **Disk Full**: Graceful degradation, user notification
2. **Permission Denied**: Fallback locations, clear error messages
3. **Network Drives**: Handle slow/unavailable network storage
4. **Concurrent Access**: File locking, atomic operations

### UI Edge Cases

1. **Terminal Resize**: Dynamic layout adjustment
2. **Unicode Content**: Proper UTF-8 handling
3. **Large Content**: Scrolling, pagination for large captures
4. **Clipboard Failures**: Graceful fallback, user notification

### Capture Edge Cases

1. **Empty Captures**: Validation, user confirmation
2. **Binary Content**: Safe handling, metadata extraction
3. **Large Files**: Size limits, compression options
4. **Network Resources**: Timeout handling, offline mode

## Testing Strategy

### Unit Tests

```python
# tests/test_markdown_writer.py
def test_safe_write_new_file():
    # Test writing to non-existent daily file
    
def test_safe_write_existing_file():
    # Test appending to existing daily file
    
def test_backup_creation():
    # Test backup file creation and cleanup
    
def test_atomic_write_failure():
    # Test rollback on write failure
```

### Integration Tests

```python
# tests/test_daemon_integration.py
def test_daemon_startup():
    # Test daemon starts and creates socket
    
def test_keybind_trigger():
    # Test trigger script communicates with daemon
    
def test_capture_workflow():
    # Test complete capture workflow end-to-end
```

### Manual Testing Checklist

- [ ] Daemon starts without errors
- [ ] Keybinds trigger capture UI
- [ ] All modalities capture correctly
- [ ] Files written to correct location
- [ ] No existing files overwritten
- [ ] UI responsive with semantic keybindings
- [ ] Graceful error handling
- [ ] Memory usage remains stable

## Performance Requirements

### Response Time Targets

- **Keybind to UI**: < 100ms
- **Capture Save**: < 500ms
- **Daemon Startup**: < 2s
- **Memory Usage**: < 50MB steady state

### Optimization Strategies

1. **Lazy Loading**: Load UI components on demand
2. **Background Processing**: Async file operations
3. **Caching**: Context/tag suggestions cached
4. **Resource Cleanup**: Regular cleanup of temporary files

## Security Considerations

### Data Protection

1. **File Permissions**: Restrict access to capture files (600)
2. **Socket Security**: Unix socket with proper permissions
3. **Temporary Files**: Secure cleanup of temporary data
4. **Clipboard Handling**: Safe handling of sensitive clipboard content

### Process Security

1. **Privilege Separation**: Run with minimal required permissions
2. **Input Validation**: Sanitize all user inputs
3. **Resource Limits**: Prevent resource exhaustion attacks
4. **Error Information**: Avoid leaking sensitive info in errors

## Future Enhancements

### Phase 2 Features (Optional)

1. **Context Auto-Detection**: AI-powered context suggestions
2. **Smart Tagging**: Automatic tag extraction from content
3. **Cross-Device Sync**: Sync captures across devices
4. **Plugin System**: Extensible capture modalities
5. **Search Integration**: Basic search within captures
6. **Export Options**: Export to various formats

### Extensibility Points

1. **Capture Plugins**: Interface for new capture types
2. **UI Themes**: Customizable ncurses themes
3. **Storage Backends**: Alternative storage formats
4. **Notification System**: Pluggable notification methods

## Conclusion

This design specification provides a comprehensive blueprint for implementing a lightweight, terminal-based knowledge capture daemon that integrates seamlessly with existing Obsidian workflows while providing instant, keyboard-driven capture capabilities on NixOS + Hyprland.

The system prioritizes:
- **Speed**: Instant response through background daemon
- **Safety**: Comprehensive file safety and backup mechanisms  
- **Usability**: Semantic keybindings and intuitive terminal UI
- **Reversibility**: Pure markdown storage compatible with Obsidian
- **Maintainability**: Clean architecture and comprehensive testing

Implementation should follow this specification closely while allowing for iterative improvements based on user feedback and real-world usage patterns.

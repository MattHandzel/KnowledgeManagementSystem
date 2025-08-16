# Repository Read-through: KnowledgeManagementSystem (Terminal Capture Daemon)

This document provides a thorough walkthrough of the repository’s intent, architecture, modules, data model, flows, and integration points. It is intended as a high-level orientation and a practical guide for contributors.

## Overview

The system is a terminal-based, keyboard-driven knowledge capture daemon designed for NixOS + Hyprland. It offers an instant popup capture interface with semantic keybindings and stores captures as individual Markdown files with YAML frontmatter. The approach prioritizes speed, reversibility (plain markdown), and compatibility with tools like Obsidian.

Key goals:
- Ultra-fast capture with a background daemon and Unix socket.
- ncurses terminal UI with semantic, vim-inspired keybindings.
- Individual idea files with safe, atomic writes and unique IDs.
- Multimodal inputs (text, clipboard, screenshot, audio, files).
- Nix-based development and Hyprland integration via keybindings.

Primary user flow:
Hyprland keybind → trigger_capture.py → Unix socket → capture_daemon.py (ncurses UI) → YAML-frontmatter markdown file in ~/notes/capture/raw_capture

References:
- README: <ref_file file="/home/ubuntu/repos/KnowledgeManagementSystem/README.md" />
- Design Specification: <ref_file file="/home/ubuntu/repos/KnowledgeManagementSystem/DESIGN_SPECIFICATION.md" />

## Architecture

System components:
- Capture Daemon/UI: capture_daemon.py runs a long-lived daemon and provides an ncurses UI for capture. It coordinates data collection and file writes through SafeMarkdownWriter.
- Trigger Script: trigger_capture.py is invoked by Hyprland keybinds to signal the daemon via Unix domain socket to show the capture UI or perform specific modes (quick, multimodal, voice, screenshot, clipboard).
- Markdown Writer: markdown_writer.py formats, writes, and manages idea markdown files atomically, including media handling and backups.
- Keybindings: keybindings.py maps terminal key events to high-level UI actions. Modes include INSERT, NORMAL, BROWSE, EDIT, and field-specific handling.
- Configuration: config.yaml controls vault path, capture directories, media directory, daemon socket path, UI behavior, and capture options.

Flow:
1) Hyprland executes trigger_capture.py with a command (e.g., quick).
2) The trigger connects to the daemon (or starts it if down) via Unix socket at /tmp/capture_daemon.sock.
3) The daemon launches ncurses UI for capture.
4) User edits content and metadata, toggles modalities, and saves with Ctrl+S.
5) SafeMarkdownWriter writes a new markdown file to ~/notes/capture/raw_capture, copying media to ~/notes/capture/raw_capture/media.

Key code references:
- Capture UI & Daemon: <ref_snippet file="/home/ubuntu/repos/KnowledgeManagementSystem/capture_daemon.py" lines="26-45" />
- Daemon management: <ref_snippet file="/home/ubuntu/repos/KnowledgeManagementSystem/capture_daemon.py" lines="836-888" />
- Keybindings map & handlers: <ref_snippet file="/home/ubuntu/repos/KnowledgeManagementSystem/keybindings.py" lines="31-66" />
- Content editing keys: <ref_snippet file="/home/ubuntu/repos/KnowledgeManagementSystem/keybindings.py" lines="129-166" />
- Safe writes & formatting: <ref_snippet file="/home/ubuntu/repos/KnowledgeManagementSystem/markdown_writer.py" lines="16-36" />
- YAML formatting for captures: <ref_snippet file="/home/ubuntu/repos/KnowledgeManagementSystem/markdown_writer.py" lines="122-181" />
- Trigger script socket behavior: <ref_snippet file="/home/ubuntu/repos/KnowledgeManagementSystem/trigger_capture.py" lines="15-46" />

## Key Modules

### capture_daemon.py
- CaptureUI provides the ncurses-based interface: content area, context, tags, modalities, help overlay, idea list (browse/edit mode), and cursor/scroll handling.
- Integrates SemanticKeybindings for intuitive keyboard-driven interactions.
- Works with SafeMarkdownWriter for file operations and geolocation for metadata.
- CaptureDaemon wraps socket server responsibilities (start, receive commands, show UI, cleanup).

Highlights:
- Modalities: text, clipboard, screenshot, audio, files.
- Browse/Edit modes: list existing ideas, preview, and load file for editing.
- Error notification path may use notify-send (see UI tests).

### keybindings.py
- Defines UIMode and Field enums.
- SemanticKeybindings maps curses key codes and control keys to semantic actions.
- Field-specific handlers for content editing, context/tags/sources, modalities selection, and idea list navigation.
- HelpDisplay returns formatted help overlay text.

### markdown_writer.py
- Ensures capture_dir and media_dir exist.
- Writes captures as individual markdown files named by capture_id (timestamp-based) with unique resolution on conflicts.
- format_capture composes YAML frontmatter and sections: Content, Clipboard, Media.
- Atomic write behaviors with temporary files and replacement to avoid partial writes.
- read_idea_file parses frontmatter/body split and lists ideas sorted by mtime.
- save_media_file copies media to media_dir with unique filenames.

### trigger_capture.py
- CaptureTrigger packs the IPC logic with retry/start-daemon behavior.
- Commands: quick, multimodal, voice, screenshot, clipboard, and daemon status/stop.
- start_daemon_and_retry boots the daemon and retries the socket command.

### geolocation.py
- Optional enrichment of metadata by IP geolocation using curl to ip-api.com.
- Returns latitude, longitude, city, country, timezone when successful, else None.

### Config & Nix
- config.yaml includes:
  - vault.path: "~/notes"
  - capture_dir: "capture/raw_capture"
  - media_dir: "capture/raw_capture/media"
  - daemon: socket_path, auto_start, hot_reload, debug
  - ui: theme, window_size, auto_focus_content, show_help
  - capture: auto_detect_modalities, context_suggestions, tag_suggestions
- shell.nix and flake.nix define dev/build environments with ncurses, capture tools (grim, slurp, wl-clipboard, wf-recorder, alsa-utils), libnotify, and Python tooling.

## Data Model

Each capture is a single markdown file with YAML frontmatter:

Frontmatter (typical fields):
- timestamp: ISO 8601 string
- capture_id: unique id based on timestamp
- modalities: e.g., ["text", "clipboard", "screenshot"]
- context: object with fields like activity, location, device
- sources: array of strings, e.g., ["book: Deep Work"]
- location: object or null (from geolocation)
- metadata: freeform object for extras
- processing_status: defaults to "raw"
- importance: numeric, defaults 0.5
- tags: array of strings

Body Sections (optional based on capture):
- ## Content
- ## Clipboard
- ## Media (bullet list with links to media files)

Formatting logic reference: <ref_snippet file="/home/ubuntu/repos/KnowledgeManagementSystem/markdown_writer.py" lines="122-181" />

## Storage Structure

Default vault layout:
- ~/notes/capture/raw_capture/*.md
- ~/notes/capture/raw_capture/media/*

From README File Structure: <ref_snippet file="/home/ubuntu/repos/KnowledgeManagementSystem/README.md" lines="65-75" />

## UI & Keybindings

- Content editing with arrow keys, Home/End, Page Up/Down, Ctrl+U, Ctrl+W, Enter, Backspace/Delete.
- Fields: Content, Context, Tags, Sources, Modalities, Idea List.
- Global: Ctrl+S save, ESC cancel, F1 help, Tab/Shift+Tab navigate fields, Ctrl+B browse, Ctrl+E edit from browse, Space toggles modality in normal mode.

## Nix/Hyprland Integration

- shell.nix and flake.nix provide dependencies and shell hooks to facilitate development.
- Hyprland keybindings from README and design spec to trigger different capture modes and set window rules for the popup.
- Example binds reference trigger_capture.py with different modes and auto-start the daemon.

See:
- README Hyprland section: <ref_snippet file="/home/ubuntu/repos/KnowledgeManagementSystem/README.md" lines="36-55" />

## Testing Strategy

- Behavior tests: tests/test_capture_flows.py exercise end-to-end file writes, multimodal content, sources array, ISO timestamps, geolocation integration, uniqueness, atomic write, directory creation, media handling, error scenarios including malformed YAML and geolocation failures.
- UI integration: tests/test_ui_integration.py exercises SemanticKeybindings interactions with a mocked UI, including save/cancel flows, field navigation, modes, content editing, modalities, help, browsing, and notify-send usage.

References:
- <ref_file file="/home/ubuntu/repos/KnowledgeManagementSystem/tests/test_capture_flows.py" />
- <ref_file file="/home/ubuntu/repos/KnowledgeManagementSystem/tests/test_ui_integration.py" />

## Performance & Security

From the design spec:
- Targets: <100ms keybind-to-UI, <500ms save, <2s daemon startup, <50MB memory.
- Strategies: lazy loading, async/background processing, caching, cleanup.
- Security: file permissions, socket permissions, secure temp/cleanup, input validation, minimal privileges, avoiding sensitive leaks in errors, resource limits.

## Future Enhancements

As outlined in the design:
- Context auto-detection, smart tagging, cross-device sync, plugin system, search integration, export options, UI themes, storage backends, pluggable notifications.

## Practical Setup Notes

- Development with Nix: nix develop, run pytest tests/, black/flake8/mypy as applicable.
- Manual testing via python capture_daemon.py --daemon and trigger_capture.py commands.
- Hyprland binds provided in README.

## Web App

This repository now includes an informational React web app under client/ that presents the system’s features, architecture, and documentation links. It is a minimal landing created for orientation and visibility. See README “Web App” section for details and client/README.md for local dev/build instructions.

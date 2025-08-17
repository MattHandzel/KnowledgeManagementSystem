#!/usr/bin/env python3
"""
Safe markdown file writer with backup and conflict resolution.
Handles writing captures to daily markdown files in the vault.
"""

import os
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Optional, List
import yaml


class SafeMarkdownWriter:
    """Handles safe writing of capture data to markdown files."""

    def __init__(self, vault_path: str):
        self.vault_path = Path(vault_path).expanduser()
        self.capture_dir = self.vault_path / "capture" / "raw_capture"
        self.media_dir = self.vault_path / "capture" / "raw_capture" / "media"

        self.capture_dir.mkdir(parents=True, exist_ok=True)
        self.media_dir.mkdir(parents=True, exist_ok=True)

    def write_capture(self, capture_data: Dict[str, Any]) -> Path:
        """Write capture data to individual idea markdown file safely."""
        idea_file = self.get_idea_file(
            capture_data.get("timestamp"), capture_data.get("capture_id")
        )

        if idea_file.exists():
            idea_file = self.get_unique_idea_file(
                capture_data.get("timestamp"), capture_data.get("capture_id")
            )

        formatted_content = self.format_capture(capture_data)

        return self.atomic_write_new(idea_file, formatted_content)

    def get_idea_file(
        self,
        timestamp: Optional[datetime] = None,
        capture_id: Optional[str] = None,
    ) -> Path:
        """Get the individual idea markdown file path."""
        if timestamp is None:
            timestamp = datetime.now()

        if capture_id is None:
            capture_id = self.generate_capture_id(timestamp)

        filename = f"{capture_id}.md"
        return self.capture_dir / filename

    def get_unique_idea_file(
        self,
        timestamp: Optional[datetime] = None,
        capture_id: Optional[str] = None,
    ) -> Path:
        """Get a unique idea file path if the original exists."""
        if timestamp is None:
            timestamp = datetime.now()

        if capture_id is None:
            capture_id = self.generate_capture_id(timestamp)

        counter = 1
        while True:
            filename = f"{capture_id}_{counter}.md"
            idea_file = self.capture_dir / filename
            if not idea_file.exists():
                return idea_file
            counter += 1

    def create_backup(self, file_path: Path) -> Path:
        """Create a timestamped backup of the file."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = file_path.with_suffix(f".backup.{timestamp}")

        try:
            shutil.copy2(file_path, backup_path)
            self.cleanup_old_backups(file_path)
            return backup_path
        except Exception as e:
            print(f"Warning: Could not create backup: {e}")
            return file_path

    def cleanup_old_backups(self, original_file: Path, keep_count: int = 5):
        """Clean up old backup files, keeping only the most recent ones."""
        backup_pattern = f"{original_file.stem}.backup.*"
        backup_files = list(original_file.parent.glob(backup_pattern))

        if len(backup_files) > keep_count:
            backup_files.sort(key=lambda f: f.stat().st_mtime)

            for old_backup in backup_files[:-keep_count]:
                try:
                    old_backup.unlink()
                except Exception as e:
                    print(f"Warning: Could not remove old backup " f"{old_backup}: {e}")

    def atomic_write_new(self, target_file: Path, content: str) -> Path:
        """Perform atomic write operation for new file creation."""
        temp_file = target_file.with_suffix(".tmp")

        try:
            with temp_file.open("w", encoding="utf-8") as f:
                f.write(content)

            temp_file.replace(target_file)
            return target_file

        except Exception as e:
            temp_file.unlink(missing_ok=True)
            raise Exception(f"Failed to write capture: {e}")

    def atomic_write(self, target_file: Path, content: str) -> Path:
        """Perform atomic write operation with rollback on failure."""
        temp_file = target_file.with_suffix(".tmp")

        try:
            with temp_file.open("a", encoding="utf-8") as f:
                f.write(content)

            temp_file.replace(target_file)
            return target_file

        except Exception as e:
            temp_file.unlink(missing_ok=True)
            raise Exception(f"Failed to write capture: {e}")

    def format_capture(self, capture_data: Dict[str, Any]) -> str:
        """Format capture data as markdown with YAML frontmatter."""
        ts_input = capture_data.get("timestamp")
        if ts_input is None:
            ts_now = datetime.now(timezone.utc).replace(microsecond=0)
            iso_ts = ts_now.isoformat()
            timestamp_for_id = ts_now
        else:
            iso_ts = ts_input.isoformat()
            timestamp_for_id = ts_input
        capture_id = capture_data.get(
            "capture_id", self.generate_capture_id(timestamp_for_id)
        )

        frontmatter = {
            "timestamp": iso_ts,
            "id": capture_id,
            "aliases": [capture_id],
            "capture_id": capture_id,
            "modalities": capture_data.get("modalities", ["text"]),
            "context": capture_data.get("context", {}),
            "sources": capture_data.get("sources", []),
            "location": capture_data.get("location"),
            "metadata": capture_data.get("metadata", {}),
            "processing_status": "raw",
            "importance": capture_data.get("importance", None),
            "tags": capture_data.get("tags", []),
            "created_date": capture_data.get(
                "created_date", timestamp_for_id.date().isoformat()
            ),
            "last_edited_date": capture_data.get(
                "last_edited_date", timestamp_for_id.date().isoformat()
            ),
        }

        content_sections = []

        if str(capture_data.get("content", "")).strip():
            content_sections.append(f"## Content\n{capture_data.get('content')}\n")

        clip = str(capture_data.get("clipboard", "") or "")
        if clip.strip():
            if clip.startswith("```") or "\n" in clip:
                content_sections.append(f"## Clipboard\n{clip}\n")
            else:
                content_sections.append(f"## Clipboard\n```\n{clip}\n```\n")

        media_files = capture_data.get("media_files", [])
        if media_files:
            media_section = "## Media\n"
            for media_file in media_files:
                media_type = media_file.get("type", "file")
                media_path = media_file.get("path", "")
                relative_path = self.get_relative_media_path(media_path)

                if media_type == "screenshot":
                    media_section += f"- Screenshot: ![Screenshot]({relative_path})\n"
                elif media_type == "audio":
                    media_section += f"- Audio: [Audio Recording]({relative_path})\n"
                elif media_type == "image":
                    media_section += f"- Image: ![Image]({relative_path})\n"
                else:
                    media_section += f"- File: [Attachment]({relative_path})\n"

            content_sections.append(media_section)

        yaml_content = yaml.dump(frontmatter, default_flow_style=False, sort_keys=False)
        formatted_content = f"---\n{yaml_content}---\n{''.join(content_sections)}"
        return formatted_content

    def generate_capture_id(self, timestamp: datetime) -> str:
        """Generate a unique capture ID based on timestamp."""
        return timestamp.strftime("%Y%m%d_%H%M%S_%f")[
            :-3
        ]  # Remove last 3 microsecond digits

    def get_relative_media_path(self, media_path: str) -> str:
        """Convert absolute media path to relative path from capture dir."""
        media_path_obj = Path(media_path)
        try:
            relative_path = os.path.relpath(media_path_obj, self.capture_dir)
            return relative_path
        except ValueError:
            return str(media_path_obj)

    def list_ideas(self) -> List[Path]:
        """List all existing idea files sorted by modification time."""
        idea_files = list(self.capture_dir.glob("*.md"))
        return sorted(idea_files, key=lambda f: f.stat().st_mtime, reverse=True)

    def read_idea_file(self, idea_file: Path) -> Optional[Dict[str, Any]]:
        """Read and parse an existing idea file."""
        try:
            with idea_file.open("r", encoding="utf-8") as f:
                content = f.read()

            if content.startswith("---"):
                parts = content.split("---", 2)
                if len(parts) >= 3:
                    frontmatter = yaml.safe_load(parts[1])
                    body = parts[2].strip()

                    return {
                        "frontmatter": frontmatter,
                        "body": body,
                        "file_path": idea_file,
                    }
        except Exception as e:
            print(f"Error reading idea file {idea_file}: {e}")
        return None

    def save_media_file(self, source_path: Path, media_type: str) -> Path:
        """Save media file to media directory with unique name."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]

        if source_path.suffix:
            extension = source_path.suffix
        else:
            extension_map = {
                "screenshot": ".png",
                "audio": ".wav",
                "image": ".png",
                "video": ".mp4",
            }
            extension = extension_map.get(media_type, ".bin")

        target_filename = f"{timestamp}_{media_type}{extension}"
        target_path = self.media_dir / target_filename

        counter = 1
        while target_path.exists():
            target_filename = f"{timestamp}_{media_type}_{counter}{extension}"
            target_path = self.media_dir / target_filename
            counter += 1

        try:
            shutil.copy2(source_path, target_path)
            return target_path
        except Exception as e:
            raise Exception(f"Failed to save media file: {e}")


if __name__ == "__main__":
    writer = SafeMarkdownWriter("~/notes")

    test_capture = {
        "timestamp": datetime.now(),
        "content": "This is a test capture",
        "context": {"activity": "testing", "location": "home"},
        "tags": ["test", "development"],
        "modalities": ["text"],
    }

    try:
        result_file = writer.write_capture(test_capture)
        print(f"Test capture written to: {result_file}")
    except Exception as e:
        print(f"Test failed: {e}")

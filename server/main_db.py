import sqlite3
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import difflib


@dataclass
class SuggestionItem:
    value: str
    count: int
    last_used: datetime
    color: str = ""


class MainDatabase:
    """Main database for comprehensive tracking of all capture data."""

    def __init__(self, db_path: str = "main.db"):
        self.db_path = Path(db_path)
        self.init_database()

    def init_database(self):
        """Initialize the database with comprehensive tracking tables."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS captures (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    capture_id TEXT UNIQUE NOT NULL,
                    timestamp TEXT NOT NULL,
                    content TEXT,
                    context TEXT,
                    modalities TEXT,
                    location TEXT,
                    metadata TEXT,
                    created_date TEXT,
                    last_edited_date TEXT,
                    file_path TEXT
                )
            """
            )

            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS tags (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    value TEXT NOT NULL,
                    capture_id TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    FOREIGN KEY (capture_id) REFERENCES captures (capture_id)
                )
            """
            )

            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS sources (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    value TEXT NOT NULL,
                    capture_id TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    FOREIGN KEY (capture_id) REFERENCES captures (capture_id)
                )
            """
            )

            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS contexts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    value TEXT NOT NULL,
                    capture_id TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    FOREIGN KEY (capture_id) REFERENCES captures (capture_id)
                )
            """
            )

            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS media_files (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    capture_id TEXT NOT NULL,
                    file_path TEXT NOT NULL,
                    file_type TEXT,
                    file_name TEXT,
                    timestamp TEXT NOT NULL,
                    FOREIGN KEY (capture_id) REFERENCES captures (capture_id)
                )
            """
            )

            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS suggestion_feedback (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    field_type TEXT NOT NULL,
                    value TEXT NOT NULL,
                    action TEXT NOT NULL,
                    confidence REAL,
                    edited_value TEXT,
                    content_hash TEXT,
                    timestamp TEXT NOT NULL
                )
            """
            )

            conn.execute("CREATE INDEX IF NOT EXISTS idx_tags_value ON tags (value)")
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_sources_value ON sources (value)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_contexts_value ON contexts (value)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_captures_timestamp "
                "ON captures (timestamp)"
            )

            conn.commit()

    def store_capture_data(self, capture_data: Dict[str, Any]):
        """Store comprehensive capture data in the database."""
        print(f"DEBUG: store_capture_data called with: {capture_data}")
        timestamp = datetime.now(timezone.utc).isoformat()
        
        # Ensure capture_id is never None - use timestamp as fallback
        capture_id = capture_data.get("capture_id")
        if not capture_id:  # Handle None, empty string, etc.
            capture_id = timestamp
            # Also update the capture data dictionary with the generated ID
            capture_data["capture_id"] = capture_id
            
        print(f"DEBUG: Using capture_id: {capture_id}, timestamp: {timestamp}")

        with sqlite3.connect(self.db_path) as conn:
            content = capture_data.get("content", "")
            context = capture_data.get("context", "")
            tags = capture_data.get("tags", [])
            print(
                f"DEBUG: Inserting capture with content: '{content}', "
                f"context: '{context}', tags: {tags}"
            )
            conn.execute(
                """
                INSERT OR REPLACE INTO captures 
                (capture_id, timestamp, content, context, modalities, location, 
                 metadata, created_date, last_edited_date, file_path)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    capture_id,
                    timestamp,
                    capture_data.get("content", ""),
                    capture_data.get("context", ""),
                    json.dumps(capture_data.get("modalities", [])),
                    json.dumps(capture_data.get("location")),
                    json.dumps(capture_data.get("metadata", {})),
                    capture_data.get("created_date", ""),
                    capture_data.get("last_edited_date", ""),
                    capture_data.get("file_path", ""),
                ),
            )
            print("DEBUG: Capture inserted successfully")

            tags = capture_data.get("tags", [])
            if isinstance(tags, str):
                tags = [t.strip() for t in tags.split(",") if t.strip()]
            for tag in tags:
                if tag.strip():
                    conn.execute(
                        """
                        INSERT INTO tags (value, capture_id, timestamp)
                        VALUES (?, ?, ?)
                    """,
                        (tag.strip(), capture_id, timestamp),
                    )

            sources = capture_data.get("sources", [])
            if isinstance(sources, str):
                sources = [s.strip() for s in sources.split(",") if s.strip()]
            for source in sources:
                if source.strip():
                    conn.execute(
                        """
                        INSERT INTO sources (value, capture_id, timestamp)
                        VALUES (?, ?, ?)
                    """,
                        (source.strip(), capture_id, timestamp),
                    )

            context = capture_data.get("context", "")
            if isinstance(context, str) and context.strip():
                conn.execute(
                    """
                    INSERT INTO contexts (value, capture_id, timestamp)
                    VALUES (?, ?, ?)
                """,
                    (context.strip(), capture_id, timestamp),
                )

            media_files = capture_data.get("media_files", [])
            for media_file in media_files:
                conn.execute(
                    """
                    INSERT INTO media_files 
                    (capture_id, file_path, file_type, file_name, timestamp)
                    VALUES (?, ?, ?, ?, ?)
                """,
                    (
                        capture_id,
                        media_file.get("path", ""),
                        media_file.get("type", ""),
                        media_file.get("name", ""),
                        timestamp,
                    ),
                )

            conn.commit()
            print("DEBUG: Database transaction committed successfully")

    def store_suggestion_feedback(self, field_type: str, value: str, action: str, confidence: Optional[float] = None, edited_value: Optional[str] = None, content_hash: Optional[str] = None):
        ts = datetime.now(timezone.utc).isoformat()
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO suggestion_feedback (field_type, value, action, confidence, edited_value, content_hash, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (field_type, value, action, confidence, edited_value, content_hash, ts),
            )
            conn.commit()

    def get_suggestions(
        self, field_type: str, query: str = "", limit: int = 10
    ) -> List[SuggestionItem]:
        """Get suggestions for a field type with fuzzy matching and sorting."""
        table_map = {"tag": "tags", "source": "sources", "context": "contexts"}

        if field_type not in table_map:
            return []

        table = table_map[field_type]

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                f"""
                SELECT value, COUNT(*) as count, MAX(timestamp) as last_used
                FROM {table}
                GROUP BY value
                ORDER BY last_used DESC
            """
            )

            all_suggestions = []
            for row in cursor.fetchall():
                value, count, last_used = row
                try:
                    last_used_dt = datetime.fromisoformat(
                        last_used.replace("Z", "+00:00")
                    )
                except Exception:
                    last_used_dt = datetime.now(timezone.utc)

                all_suggestions.append(
                    SuggestionItem(value=value, count=count, last_used=last_used_dt)
                )

        if not query.strip():
            return all_suggestions[:limit]

        query_lower = query.lower()
        scored_suggestions = []

        for suggestion in all_suggestions:
            value_lower = suggestion.value.lower()

            score = 0

            if value_lower == query_lower:
                score = 1000
            elif value_lower.startswith(query_lower):
                score = 800
            elif query_lower in value_lower:
                score = 600
            else:
                similarity = difflib.SequenceMatcher(
                    None, query_lower, value_lower
                ).ratio()
                if similarity > 0.3:  # Only include if similarity is above threshold
                    score = int(similarity * 400)
                else:
                    continue

            count_boost = min(suggestion.count * 10, 100)

            days_ago = (datetime.now(timezone.utc) - suggestion.last_used).days
            recency_boost = max(0, 50 - days_ago)

            final_score = score + count_boost + recency_boost
            scored_suggestions.append((final_score, suggestion))

        scored_suggestions.sort(key=lambda x: x[0], reverse=True)
        return [suggestion for _, suggestion in scored_suggestions[:limit]]

    def suggestion_exists(self, value: str, field_type: str) -> bool:
        """Check if a suggestion value exists in the database."""
        table_map = {"tag": "tags", "source": "sources", "context": "contexts"}

        if field_type not in table_map:
            return False

        table = table_map[field_type]

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                f"""
                SELECT COUNT(*) FROM {table} WHERE value = ?
            """,
                (value,),
            )

            count = cursor.fetchone()[0]
            return count > 0

    def _ensure_last_used_table_exists(self):
        """Ensure the last_used_values table exists."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS last_used_values (
                    key TEXT PRIMARY KEY,
                    value TEXT,
                    timestamp TEXT
                )
                """
            )

    def store_last_used_values(self, values: Dict[str, List[str]], ai_suggested: Dict[str, List[str]] = None):
        """Store last used values for tags and sources for persistence between captures.
        
        Args:
            values: Dictionary containing user-confirmed tags and sources
            ai_suggested: Dictionary containing AI-suggested tags and sources that haven't been confirmed
        """
        self._ensure_last_used_table_exists()
        timestamp = datetime.now(timezone.utc).isoformat()
        ai_suggested = ai_suggested or {}
        
        with sqlite3.connect(self.db_path) as conn:
            # Store user-added tags
            if "tags" in values and values["tags"]:
                conn.execute(
                    """INSERT OR REPLACE INTO last_used_values (key, value, timestamp) VALUES (?, ?, ?)""",
                    ("user_tags", json.dumps(values["tags"]), timestamp)
                )
            
            # Store AI-suggested tags
            if "tags" in ai_suggested and ai_suggested["tags"]:
                conn.execute(
                    """INSERT OR REPLACE INTO last_used_values (key, value, timestamp) VALUES (?, ?, ?)""",
                    ("ai_tags", json.dumps(ai_suggested["tags"]), timestamp)
                )
            
            # Store user-added sources
            if "sources" in values and values["sources"]:
                conn.execute(
                    """INSERT OR REPLACE INTO last_used_values (key, value, timestamp) VALUES (?, ?, ?)""",
                    ("user_sources", json.dumps(values["sources"]), timestamp)
                )
                
            # Store AI-suggested sources
            if "sources" in ai_suggested and ai_suggested["sources"]:
                conn.execute(
                    """INSERT OR REPLACE INTO last_used_values (key, value, timestamp) VALUES (?, ?, ?)""",
                    ("ai_sources", json.dumps(ai_suggested["sources"]), timestamp)
                )

    def get_most_recent_values(self) -> Dict[str, List[str]]:
        """Get last used values for tags and sources for persistence between captures.
        
        Returns a dictionary with keys:
        - user_tags: Tags added by the user
        - ai_tags: Tags suggested by AI
        - user_sources: Sources added by the user
        - ai_sources: Sources suggested by AI
        - tags: Combined tags (for backward compatibility)
        - sources: Combined sources (for backward compatibility)
        - context: Context from last capture
        """
        result: Dict[str, List[str]] = {}
        self._ensure_last_used_table_exists()

        with sqlite3.connect(self.db_path) as conn:
            # Get user-added tags
            cursor = conn.execute(
                """SELECT value FROM last_used_values WHERE key = 'user_tags' LIMIT 1"""
            )
            row = cursor.fetchone()
            user_tags = []
            if row and row[0]:
                try:
                    user_tags = json.loads(row[0])
                    result["user_tags"] = user_tags
                except json.JSONDecodeError:
                    pass

            # Get AI-suggested tags
            cursor = conn.execute(
                """SELECT value FROM last_used_values WHERE key = 'ai_tags' LIMIT 1"""
            )
            row = cursor.fetchone()
            ai_tags = []
            if row and row[0]:
                try:
                    ai_tags = json.loads(row[0])
                    result["ai_tags"] = ai_tags
                except json.JSONDecodeError:
                    pass
                    
            # Combined tags for backward compatibility
            if user_tags or ai_tags:
                result["tags"] = user_tags + [tag for tag in ai_tags if tag not in user_tags]

            # Get user-added sources
            cursor = conn.execute(
                """SELECT value FROM last_used_values WHERE key = 'user_sources' LIMIT 1"""
            )
            row = cursor.fetchone()
            user_sources = []
            if row and row[0]:
                try:
                    user_sources = json.loads(row[0])
                    result["user_sources"] = user_sources
                except json.JSONDecodeError:
                    pass

            # Get AI-suggested sources
            cursor = conn.execute(
                """SELECT value FROM last_used_values WHERE key = 'ai_sources' LIMIT 1"""
            )
            row = cursor.fetchone()
            ai_sources = []
            if row and row[0]:
                try:
                    ai_sources = json.loads(row[0])
                    result["ai_sources"] = ai_sources
                except json.JSONDecodeError:
                    pass
                    
            # Combined sources for backward compatibility
            if user_sources or ai_sources:
                result["sources"] = user_sources + [source for source in ai_sources if source not in user_sources]
                
            # Check for old format tags/sources for migration
            if "tags" not in result:
                cursor = conn.execute(
                    """SELECT value FROM last_used_values WHERE key = 'tags' LIMIT 1"""
                )
                row = cursor.fetchone()
                if row and row[0]:
                    try:
                        tags = json.loads(row[0])
                        result["tags"] = tags
                        result["user_tags"] = tags
                    except json.JSONDecodeError:
                        pass
                        
            if "sources" not in result:
                cursor = conn.execute(
                    """SELECT value FROM last_used_values WHERE key = 'sources' LIMIT 1"""
                )
                row = cursor.fetchone()
                if row and row[0]:
                    try:
                        sources = json.loads(row[0])
                        result["sources"] = sources
                        result["user_sources"] = sources
                    except json.JSONDecodeError:
                        pass

            # For backwards compatibility, get context from last capture
            cursor = conn.execute(
                """SELECT capture_id FROM captures ORDER BY timestamp DESC LIMIT 1"""
            )
            row = cursor.fetchone()
            if row:
                most_recent_capture_id = row[0]
                cursor = conn.execute(
                    """SELECT value FROM contexts WHERE capture_id = ? ORDER BY timestamp DESC LIMIT 1""",
                    (most_recent_capture_id,),
                )
                row = cursor.fetchone()
                if row:
                    result["context"] = [row[0]]

        return result

    def get_capture_statistics(self) -> Dict[str, Any]:
        """Get comprehensive statistics about captures."""
        with sqlite3.connect(self.db_path) as conn:
            stats = {}

            cursor = conn.execute("SELECT COUNT(*) FROM captures")
            stats["total_captures"] = cursor.fetchone()[0]

            cursor = conn.execute("SELECT COUNT(DISTINCT value) FROM tags")
            stats["unique_tags"] = cursor.fetchone()[0]

            cursor = conn.execute("SELECT COUNT(DISTINCT value) FROM sources")
            stats["unique_sources"] = cursor.fetchone()[0]

            cursor = conn.execute("SELECT COUNT(DISTINCT value) FROM contexts")
            stats["unique_contexts"] = cursor.fetchone()[0]

            cursor = conn.execute(
                """
                SELECT value, COUNT(*) as count 
                FROM tags 
                GROUP BY value 
                ORDER BY count DESC 
                LIMIT 10
            """
            )
            stats["top_tags"] = cursor.fetchall()

            cursor = conn.execute(
                """
                SELECT value, COUNT(*) as count 
                FROM sources 
                GROUP BY value 
                ORDER BY count DESC 
                LIMIT 10
            """
            )
            stats["top_sources"] = cursor.fetchall()

            return stats

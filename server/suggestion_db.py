"""
Database system for storing and retrieving tag, source, and context suggestions.
Implements basic storage with recency and text matching capabilities.
"""

import sqlite3
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import difflib


@dataclass
class SuggestionItem:
    """Represents a suggestion item with metadata."""
    value: str
    field_type: str  # 'tag', 'source', 'context'
    count: int
    last_used: datetime
    color: str
    created_at: datetime


class SuggestionDatabase:
    """Manages suggestion storage and retrieval."""
    
    def __init__(self, db_path: str = "suggestions.db"):
        self.db_path = Path(db_path)
        self.init_database()
    
    def init_database(self):
        """Initialize the database with required tables."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS suggestions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    value TEXT NOT NULL,
                    field_type TEXT NOT NULL,
                    count INTEGER DEFAULT 1,
                    last_used TIMESTAMP NOT NULL,
                    color TEXT DEFAULT '#6c757d',
                    created_at TIMESTAMP NOT NULL,
                    UNIQUE(value, field_type)
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_field_type ON suggestions(field_type)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_last_used ON suggestions(last_used DESC)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_count ON suggestions(count DESC)
            """)
    
    def store_capture_data(self, capture_data: Dict[str, Any]):
        """Store tags, sources, and context from a capture."""
        now = datetime.now(timezone.utc)
        
        tags = capture_data.get('tags', [])
        if isinstance(tags, str):
            tags = [t.strip() for t in tags.split(',') if t.strip()]
        for tag in tags:
            self._upsert_suggestion(tag, 'tag', now)
        
        sources = capture_data.get('sources', [])
        if isinstance(sources, str):
            sources = [s.strip() for s in sources.split(',') if s.strip()]
        for source in sources:
            self._upsert_suggestion(source, 'source', now)
        
        context = capture_data.get('context', {})
        if isinstance(context, dict):
            for key, value in context.items():
                if value:
                    context_item = f"{key}: {value}"
                    self._upsert_suggestion(context_item, 'context', now)
        elif isinstance(context, str) and context.strip():
            self._upsert_suggestion(context.strip(), 'context', now)
    
    def _upsert_suggestion(self, value: str, field_type: str, timestamp: datetime):
        """Insert or update a suggestion item."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                UPDATE suggestions 
                SET count = count + 1, last_used = ?
                WHERE value = ? AND field_type = ?
            """, (timestamp.isoformat(), value, field_type))
            
            if cursor.rowcount == 0:
                conn.execute("""
                    INSERT INTO suggestions (value, field_type, count, last_used, created_at)
                    VALUES (?, ?, 1, ?, ?)
                """, (value, field_type, timestamp.isoformat(), timestamp.isoformat()))
    
    def get_suggestions(self, field_type: str, query: str = "", limit: int = 10) -> List[SuggestionItem]:
        """Get suggestions for a field type, optionally filtered by query."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            
            if query.strip():
                cursor = conn.execute("""
                    SELECT * FROM suggestions 
                    WHERE field_type = ?
                    ORDER BY count DESC, last_used DESC
                """, (field_type,))
                
                all_items = cursor.fetchall()
                
                matches = []
                query_lower = query.lower()
                
                for row in all_items:
                    value_lower = row['value'].lower()
                    
                    if query_lower == value_lower:
                        score = 1000
                    elif value_lower.startswith(query_lower):
                        score = 500
                    elif query_lower in value_lower:
                        score = 200
                    else:
                        ratio = difflib.SequenceMatcher(None, query_lower, value_lower).ratio()
                        if ratio > 0.6:  # Only include if similarity > 60%
                            score = int(ratio * 100)
                        else:
                            continue
                    
                    final_score = score + (row['count'] * 10) + (
                        (datetime.now(timezone.utc) - datetime.fromisoformat(row['last_used'])).days * -1
                    )
                    
                    matches.append((final_score, row))
                
                matches.sort(key=lambda x: x[0], reverse=True)
                rows = [match[1] for match in matches[:limit]]
            else:
                cursor = conn.execute("""
                    SELECT * FROM suggestions 
                    WHERE field_type = ?
                    ORDER BY count DESC, last_used DESC
                    LIMIT ?
                """, (field_type, limit))
                rows = cursor.fetchall()
            
            return [
                SuggestionItem(
                    value=row['value'],
                    field_type=row['field_type'],
                    count=row['count'],
                    last_used=datetime.fromisoformat(row['last_used']),
                    color=row['color'],
                    created_at=datetime.fromisoformat(row['created_at'])
                )
                for row in rows
            ]
    
    def suggestion_exists(self, value: str, field_type: str) -> bool:
        """Check if a suggestion already exists in the database."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT 1 FROM suggestions 
                WHERE value = ? AND field_type = ?
            """, (value, field_type))
            return cursor.fetchone() is not None
    
    def get_stats(self) -> Dict[str, int]:
        """Get database statistics."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT field_type, COUNT(*) as count
                FROM suggestions
                GROUP BY field_type
            """)
            stats = dict(cursor.fetchall())
            
            cursor = conn.execute("SELECT COUNT(*) FROM suggestions")
            stats['total'] = cursor.fetchone()[0]
            
            return stats

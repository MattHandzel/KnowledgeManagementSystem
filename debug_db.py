#!/usr/bin/env python3
import sys

sys.path.append("server")
from main_db import MainDatabase  # noqa: E402

db = MainDatabase("server/main.db")

print("=== Database Debug Information ===")

stats = db.get_capture_statistics()
print(f"Total captures: {stats['total_captures']}")
print(f"Unique tags: {stats['unique_tags']}")
print(f"Unique sources: {stats['unique_sources']}")
print(f"Unique contexts: {stats['unique_contexts']}")

print("\n=== Testing Suggestions ===")

tag_suggestions = db.get_suggestions("tag", "", 10)
print(f"All tag suggestions: {[s.value for s in tag_suggestions]}")

tag_suggestions_mach = db.get_suggestions("tag", "mach", 10)
print(f"Tag suggestions for 'mach': {[s.value for s in tag_suggestions_mach]}")

source_suggestions = db.get_suggestions("source", "", 10)
print(f"All source suggestions: {[s.value for s in source_suggestions]}")

context_suggestions = db.get_suggestions("context", "", 10)
print(f"All context suggestions: {[s.value for s in context_suggestions]}")

print("\n=== Testing Existence Check ===")
print(
    f"Tag 'machine learning' exists: {db.suggestion_exists('machine learning', 'tag')}"
)
print(f"Tag 'testing' exists: {db.suggestion_exists('testing', 'tag')}")

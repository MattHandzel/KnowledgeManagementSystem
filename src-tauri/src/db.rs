use serde::Serialize;
use rusqlite::{params, Connection};
use std::path::PathBuf;
use chrono::{DateTime, Utc};
use crate::config::load_config;

#[derive(Debug, Clone, Serialize)]
pub struct SuggestionItem {
    pub value: String,
    pub count: i64,
    pub last_used: String,
    pub color: String,
}

#[derive(Debug, Clone, Serialize)]
pub struct Exists {
    pub exists: bool,
}

#[derive(Debug, Clone, Serialize)]
pub struct RecentValues {
    pub recent_values: serde_json::Value,
}

fn db_path() -> PathBuf {
    PathBuf::from(load_config().database.path)
}

fn init_database(conn: &Connection) {
    let _ = conn.execute_batch(
        r#"
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
        );
        CREATE TABLE IF NOT EXISTS tags (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            value TEXT NOT NULL,
            capture_id TEXT NOT NULL,
            timestamp TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS sources (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            value TEXT NOT NULL,
            capture_id TEXT NOT NULL,
            timestamp TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS contexts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            value TEXT NOT NULL,
            capture_id TEXT NOT NULL,
            timestamp TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS media_files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            capture_id TEXT NOT NULL,
            file_path TEXT NOT NULL,
            file_type TEXT,
            file_name TEXT,
            timestamp TEXT NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_tags_value ON tags (value);
        CREATE INDEX IF NOT EXISTS idx_sources_value ON sources (value);
        CREATE INDEX IF NOT EXISTS idx_contexts_value ON contexts (value);
        CREATE INDEX IF NOT EXISTS idx_captures_timestamp ON captures (timestamp);
    "#,
    );
}

pub fn store_capture_data(capture: &serde_json::Value) {
    let path = db_path();
    let conn = Connection::open(path).ok();
    if conn.is_none() {
        return;
    }
    let conn = conn.unwrap();
    init_database(&conn);

    let ts = Utc::now().to_rfc3339_opts(chrono::SecondsFormat::Secs, true);
    let capture_id = capture
        .get("capture_id")
        .and_then(|v| v.as_str())
        .unwrap_or(&ts);

    let _ = conn.execute(
        r#"
        INSERT OR REPLACE INTO captures 
        (capture_id, timestamp, content, context, modalities, location, metadata, created_date, last_edited_date, file_path)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    "#,
        params![
            capture_id,
            ts,
            capture.get("content").and_then(|v| v.as_str()).unwrap_or(""),
            capture.get("context").and_then(|v| v.as_str()).unwrap_or(""),
            serde_json::to_string(&capture.get("modalities").cloned().unwrap_or(serde_json::json!([]))).unwrap_or_default(),
            serde_json::to_string(&capture.get("location").cloned().unwrap_or(serde_json::json!(null))).unwrap_or_default(),
            serde_json::to_string(&capture.get("metadata").cloned().unwrap_or(serde_json::json!({}))).unwrap_or_default(),
            capture.get("created_date").and_then(|v| v.as_str()).unwrap_or(""),
            capture.get("last_edited_date").and_then(|v| v.as_str()).unwrap_or(""),
            capture.get("file_path").and_then(|v| v.as_str()).unwrap_or(""),
        ],
    );

    let insert_items = |table: &str, items: Vec<String>| {
        for it in items {
            if it.trim().is_empty() {
                continue;
            }
            let _ = conn.execute(
                &format!(
                    "INSERT INTO {} (value, capture_id, timestamp) VALUES (?, ?, ?)",
                    table
                ),
                params![it.trim(), capture_id, ts],
            );
        }
    };

    let tags: Vec<String> = match capture.get("tags") {
        Some(serde_json::Value::String(s)) => s
            .split(',')
            .map(|x| x.trim().to_string())
            .filter(|x| !x.is_empty())
            .collect(),
        Some(serde_json::Value::Array(arr)) => arr
            .iter()
            .filter_map(|v| v.as_str().map(|s| s.to_string()))
            .collect(),
        _ => vec![],
    };
    insert_items("tags", tags);

    let sources: Vec<String> = match capture.get("sources") {
        Some(serde_json::Value::String(s)) => s
            .split(',')
            .map(|x| x.trim().to_string())
            .filter(|x| !x.is_empty())
            .collect(),
        Some(serde_json::Value::Array(arr)) => arr
            .iter()
            .filter_map(|v| v.as_str().map(|s| s.to_string()))
            .collect(),
        _ => vec![],
    };
    insert_items("sources", sources);

    if let Some(serde_json::Value::String(ctx)) = capture.get("context") {
        if !ctx.trim().is_empty() {
            let _ = conn.execute(
                "INSERT INTO contexts (value, capture_id, timestamp) VALUES (?, ?, ?)",
                params![ctx.trim(), capture_id, ts],
            );
        }
    }

    if let Some(serde_json::Value::Array(arr)) = capture.get("media_files") {
        for m in arr {
            let obj = m.as_object().cloned().unwrap_or_default();
            let file_path = obj.get("path").and_then(|v| v.as_str()).unwrap_or("");
            let file_type = obj.get("type").and_then(|v| v.as_str()).unwrap_or("");
            let file_name = obj.get("name").and_then(|v| v.as_str()).unwrap_or("");
            let _ = conn.execute(
                r#"
                INSERT INTO media_files (capture_id, file_path, file_type, file_name, timestamp)
                VALUES (?, ?, ?, ?, ?)
            "#,
                params![capture_id, file_path, file_type, file_name, ts],
            );
        }
    }
}

pub fn get_suggestions(field: &str, query: &str, limit: usize) -> Vec<SuggestionItem> {
    let table = match field {
        "tag" => "tags",
        "source" => "sources",
        "context" => "contexts",
        _ => return vec![],
    };
    let path = db_path();
    let conn = match Connection::open(path) {
        Ok(c) => c,
        Err(_) => return vec![],
    };
    init_database(&conn);

    let mut stmt = match conn.prepare(&format!(
        "SELECT value, COUNT(*) as count, MAX(timestamp) as last_used FROM {} GROUP BY value ORDER BY last_used DESC",
        table
    )) {
        Ok(s) => s,
        Err(_) => return vec![],
    };

    let rows = stmt
        .query_map([], |row| {
            let value: String = row.get(0)?;
            let count: i64 = row.get(1)?;
            let last_used: String = row.get(2)?;
            Ok(SuggestionItem {
                value,
                count,
                last_used,
                color: "".into(),
            })
        })
        .ok();

    let mut all = vec![];
    if let Some(iter) = rows {
        for r in iter.flatten() {
            all.push(r);
        }
    }

    if query.trim().is_empty() {
        return all.into_iter().take(limit).collect();
    }

    let ql = query.to_lowercase();
    let mut scored: Vec<(i32, SuggestionItem)> = vec![];
    for s in all {
        let vl = s.value.to_lowercase();
        let mut score = 0;
        if vl == ql {
            score = 1000;
        } else if vl.starts_with(&ql) {
            score = 800;
        } else if vl.contains(&ql) {
            score = 600;
        } else {
            let common = vl.chars().zip(ql.chars()).take_while(|(a, b)| a == b).count();
            if common > 0 {
                score = (common as i32) * 50;
            } else {
                continue;
            }
        }
        let count_boost = (s.count as i32 * 10).min(100);
        score += count_boost;
        scored.push((score, s));
    }
    scored.sort_by(|a, b| b.0.cmp(&a.0));
    scored.into_iter().map(|(_, s)| s).take(limit).collect()
}

pub fn suggestion_exists(field: &str, value: &str) -> Exists {
    let table = match field {
        "tag" => "tags",
        "source" => "sources",
        "context" => "contexts",
        _ => return Exists { exists: false },
    };
    let path = db_path();
    let conn = match Connection::open(path) {
        Ok(c) => c,
        Err(_) => return Exists { exists: false },
    };
    init_database(&conn);

    let mut stmt = match conn.prepare(&format!(
        "SELECT COUNT(*) FROM {} WHERE value = ?1",
        table
    )) {
        Ok(s) => s,
        Err(_) => return Exists { exists: false },
    };

    let count: i64 = stmt
        .query_row(params![value], |row| row.get(0))
        .unwrap_or(0);

    Exists { exists: count > 0 }
}

pub fn recent_values() -> RecentValues {
    let path = db_path();
    let conn = match Connection::open(path) {
        Ok(c) => c,
        Err(_) => {
            return RecentValues {
                recent_values: serde_json::json!({}),
            }
        }
    };
    init_database(&conn);

    let capture_id: Option<String> = conn
        .query_row(
            "SELECT capture_id FROM captures ORDER BY timestamp DESC LIMIT 1",
            [],
            |row| row.get(0),
        )
        .ok();

    if capture_id.is_none() {
        return RecentValues {
            recent_values: serde_json::json!({}),
        };
    }
    let cid = capture_id.unwrap();

    let mut res = serde_json::Map::new();

    let tags: Vec<String> = conn
        .prepare(
            "SELECT value FROM tags WHERE capture_id = ?1 ORDER BY timestamp DESC",
        )
        .ok()
        .and_then(|mut s| {
            s.query_map(params![cid.clone()], |row| row.get::<_, String>(0))
                .ok()
                .map(|iter| iter.flatten().collect())
        })
        .unwrap_or_else(|| vec![]);
    if !tags.is_empty() {
        res.insert("tags".into(), serde_json::json!(tags));
    }

    let sources: Vec<String> = conn
        .prepare(
            "SELECT value FROM sources WHERE capture_id = ?1 ORDER BY timestamp DESC",
        )
        .ok()
        .and_then(|mut s| {
            s.query_map(params![cid.clone()], |row| row.get::<_, String>(0))
                .ok()
                .map(|iter| iter.flatten().collect())
        })
        .unwrap_or_else(|| vec![]);
    if !sources.is_empty() {
        res.insert("sources".into(), serde_json::json!(sources));
    }

    let context: Option<String> = conn
        .query_row(
            "SELECT value FROM contexts WHERE capture_id = ?1 ORDER BY timestamp DESC LIMIT 1",
            params![cid],
            |row| row.get(0),
        )
        .ok();
    if let Some(c) = context {
        res.insert("context".into(), serde_json::json!([c]));
    }

    RecentValues {
        recent_values: serde_json::Value::Object(res),
    }
}

use serde::Serialize;
use serde_json::Value;
use std::{fs, path::PathBuf};
use chrono::{DateTime, Utc};
use crate::config::load_config;

#[derive(Debug, Clone, Serialize)]
pub struct CaptureResult {
    pub saved_to: String,
    pub verified: bool,
}

fn generate_capture_id(ts: DateTime<Utc>) -> String {
    ts.to_rfc3339_opts(chrono::SecondsFormat::Secs, true)
}

fn get_idea_file(ts: DateTime<Utc>, capture_id: Option<&str>) -> PathBuf {
    let cfg = load_config();
    let base = PathBuf::from(&cfg.vault.path)
        .join(&cfg.vault.capture_dir);
    let id = capture_id.map(|s| s.to_string()).unwrap_or_else(|| generate_capture_id(ts));
    base.join(format!("{}.md", id))
}

fn get_unique_idea_file(ts: DateTime<Utc>, capture_id: Option<&str>) -> PathBuf {
    let mut p = get_idea_file(ts, capture_id);
    if !p.exists() {
        return p;
    }
    let mut counter = 1usize;
    loop {
        let stem = p.file_stem().unwrap().to_string_lossy().to_string();
        let parent = p.parent().unwrap().to_path_buf();
        let np = parent.join(format!("{}_{}.md", stem, counter));
        if !np.exists() {
            return np;
        }
        counter += 1;
    }
}

fn get_relative_media_path(abs: &str) -> String {
    let cfg = load_config();
    let base = PathBuf::from(&cfg.vault.path).join(&cfg.vault.capture_dir);
    let p = PathBuf::from(abs);
    match pathdiff::diff_paths(&p, base) {
        Some(rel) => rel.to_string_lossy().to_string(),
        None => abs.to_string(),
    }
}

fn format_capture(capture: &Value) -> (String, DateTime<Utc>, String) {
    let ts = if let Some(s) = capture.get("timestamp") {
        if s.is_string() {
            DateTime::parse_from_rfc3339(s.as_str().unwrap()).map(|d| d.with_timezone(&Utc)).unwrap_or_else(|_| Utc::now())
        } else {
            Utc::now()
        }
    } else {
        Utc::now()
    };
    let ts_iso = ts.to_rfc3339_opts(chrono::SecondsFormat::Secs, true);

    let capture_id = capture.get("capture_id").and_then(|v| v.as_str()).map(|s| s.to_string()).unwrap_or_else(|| generate_capture_id(ts));
    let created_date = capture.get("created_date").and_then(|v| v.as_str()).map(|s| s.to_string()).unwrap_or_else(|| ts.date_naive().to_string());
    let last_edited_date = capture.get("last_edited_date").and_then(|v| v.as_str()).map(|s| s.to_string()).unwrap_or_else(|| ts.date_naive().to_string());

    let context_entities: Vec<String> = match capture.get("context") {
        Some(Value::String(s)) => if s.is_empty() { vec![] } else { vec![s.clone()] },
        Some(Value::Object(map)) => map.values().filter_map(|v| v.as_str().map(|s| s.to_string())).collect(),
        _ => vec![],
    };

    let sources_entities: Vec<String> = match capture.get("sources") {
        Some(Value::String(s)) => s.split(',').map(|x| x.trim().to_string()).filter(|x| !x.is_empty()).collect(),
        Some(Value::Array(arr)) => arr.iter().filter_map(|v| v.as_str().map(|s| s.to_string())).collect(),
        _ => vec![],
    };

    let tags_entities: Vec<String> = match capture.get("tags") {
        Some(Value::String(s)) => s.split(',').map(|x| x.trim().to_string()).filter(|x| !x.is_empty()).collect(),
        Some(Value::Array(arr)) => arr.iter().filter_map(|v| v.as_str().map(|s| s.to_string())).collect(),
        _ => vec![],
    };

    let modalities: Vec<String> = match capture.get("modalities") {
        Some(Value::Array(arr)) => arr.iter().filter_map(|v| v.as_str().map(|s| s.to_string())).collect(),
        _ => vec!["text".to_string()],
    };

    let mut frontmatter = serde_yaml::Mapping::new();
    frontmatter.insert(serde_yaml::Value::String("timestamp".into()), serde_yaml::Value::String(ts_iso.clone()));
    frontmatter.insert(serde_yaml::Value::String("id".into()), serde_yaml::Value::String(capture_id.clone()));
    frontmatter.insert(serde_yaml::Value::String("aliases".into()), serde_yaml::to_value(vec![capture_id.clone()]).unwrap());
    frontmatter.insert(serde_yaml::Value::String("capture_id".into()), serde_yaml::Value::String(capture_id.clone()));
    frontmatter.insert(serde_yaml::Value::String("modalities".into()), serde_yaml::to_value(&modalities).unwrap());
    frontmatter.insert(serde_yaml::Value::String("context".into()), serde_yaml::to_value(&context_entities).unwrap());
    frontmatter.insert(serde_yaml::Value::String("sources".into()), serde_yaml::to_value(&sources_entities).unwrap());
    frontmatter.insert(serde_yaml::Value::String("tags".into()), serde_yaml::to_value(&tags_entities).unwrap());
    if let Some(loc) = capture.get("location") {
        frontmatter.insert(serde_yaml::Value::String("location".into()), serde_yaml::to_value(loc).unwrap_or(serde_yaml::Value::Null));
    } else {
        frontmatter.insert(serde_yaml::Value::String("location".into()), serde_yaml::Value::Null);
    }
    frontmatter.insert(serde_yaml::Value::String("metadata".into()), serde_yaml::to_value(capture.get("metadata").cloned().unwrap_or(Value::Object(Default::default()))).unwrap());
    frontmatter.insert(serde_yaml::Value::String("processing_status".into()), serde_yaml::Value::String("raw".into()));
    frontmatter.insert(serde_yaml::Value::String("created_date".into()), serde_yaml::Value::String(created_date));
    frontmatter.insert(serde_yaml::Value::String("last_edited_date".into()), serde_yaml::Value::String(last_edited_date));

    let mut sections = String::new();
    if let Some(Value::String(s)) = capture.get("content") {
        if !s.trim().is_empty() {
            sections.push_str("## Content\n");
            sections.push_str(s);
            sections.push('\n');
        }
    }
    let clip = capture.get("clipboard").and_then(|v| v.as_str()).unwrap_or("");
    if !clip.trim().is_empty() {
        if clip.starts_with("```") || clip.contains('\n') {
            sections.push_str("## Clipboard\n");
            sections.push_str(clip);
            sections.push('\n');
        } else {
            sections.push_str("## Clipboard\n```\n");
            sections.push_str(clip);
            sections.push_str("\n```\n");
        }
    }
    if let Some(Value::Array(arr)) = capture.get("media_files") {
        for m in arr {
            let obj = m.as_object().cloned().unwrap_or_default();
            let mtype = obj.get("type").and_then(|v| v.as_str()).unwrap_or("file");
            let path = obj.get("path").and_then(|v| v.as_str()).unwrap_or("");
            match mtype {
                "screenshot" => {
                    sections.push_str("## Screenshot\n");
                    sections.push_str(path);
                    sections.push('\n');
                }
                "audio" => {
                    let rel = get_relative_media_path(path);
                    sections.push_str("## Audio\n[Audio Recording](");
                    sections.push_str(&rel);
                    sections.push_str(")\n");
                }
                "image" => {
                    let rel = get_relative_media_path(path);
                    sections.push_str("## Image\n![Image](");
                    sections.push_str(&rel);
                    sections.push_str(")\n");
                }
                _ => {
                    let rel = get_relative_media_path(path);
                    sections.push_str("## File\n[Attachment](");
                    sections.push_str(&rel);
                    sections.push_str(")\n");
                }
            }
        }
    }

    let yaml_text = serde_yaml::to_string(&frontmatter).unwrap();
    let formatted = format!("---\n{}---\n{}", yaml_text, sections);
    (formatted, ts, capture_id)
}

pub fn write_capture_with(capture: Value) -> CaptureResult {
    let (content, ts, capture_id) = format_capture(&capture);
    let cfg = load_config();
    let capture_dir = PathBuf::from(&cfg.vault.path).join(&cfg.vault.capture_dir);
    let media_dir = PathBuf::from(&cfg.vault.path).join(&cfg.vault.media_dir);
    let _ = fs::create_dir_all(&capture_dir);
    let _ = fs::create_dir_all(&media_dir);

    let mut path = get_idea_file(ts, Some(&capture_id));
    if path.exists() {
        path = get_unique_idea_file(ts, Some(&capture_id));
    }
    let tmp = path.with_extension("tmp");
    if fs::write(&tmp, content.as_bytes()).is_ok() {
        let _ = fs::rename(&tmp, &path);
    } else {
        let _ = fs::remove_file(&tmp);
    }
    let ok = path.exists();
    CaptureResult {
        saved_to: path.to_string_lossy().to_string(),
        verified: ok,
    }
}

pub fn write_capture() -> CaptureResult {
    write_capture_with(serde_json::json!({}))
}

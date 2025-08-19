use tauri::Manager;
use std::{net::SocketAddr, thread};
use once_cell::sync::OnceCell;
use axum::{
    routing::{get, post},
    Router,
    response::IntoResponse,
    extract::{Path, Query, Form},
    http::StatusCode,
    Json,
};
use std::collections::HashMap;
use tower_http::cors::{Any, CorsLayer};

mod config;
mod db;
mod markdown;

static SERVER_ADDR: OnceCell<SocketAddr> = OnceCell::new();

async fn api_config() -> impl IntoResponse {
    let cfg = config::load_config();
    Json(cfg)
}

async fn api_clipboard() -> impl IntoResponse {
    use std::process::Command;
    let output = Command::new("wl-paste").arg("-t").arg("text").output();
    if let Ok(out) = output {
        if out.status.success() {
            let content = String::from_utf8_lossy(&out.stdout).to_string();
            return Json(serde_json::json!({ "content": content, "type": "text" }));
        }
    }
    Json(serde_json::json!({ "content": "", "type": "text" }))
}

async fn api_screenshot() -> impl IntoResponse {
    use std::{process::Command, fs};
    let ts = chrono::Utc::now().format("%Y%m%d_%H%M%S_%3f").to_string();
    let cfg = config::load_config();
    let media_dir = std::path::PathBuf::from(&cfg.vault.path).join(&cfg.vault.media_dir);
    let _ = fs::create_dir_all(&media_dir);
    let path = media_dir.join(format!("{}_screenshot.png", ts));
    let res = Command::new("grim").arg(path.to_string_lossy().to_string()).output();
    match res {
        Ok(out) if out.status.success() => {
            Json(serde_json::json!({ "path": path.to_string_lossy(), "success": true }))
        }
        Ok(out) => {
            let err = String::from_utf8_lossy(&out.stderr).to_string();
            Json(serde_json::json!({ "success": false, "error": if err.is_empty() { "Screenshot failed" } else { err.as_str() } }))
        }
        Err(e) => Json(serde_json::json!({ "success": false, "error": e.to_string() })),
    }
}

#[derive(serde::Deserialize)]
struct CaptureForm {
    #[serde(default)]
    content: String,
    #[serde(default)]
    context: String,
    #[serde(default)]
    tags: String,
    #[serde(default)]
    sources: String,
    #[serde(default)]
    modalities: String,
    #[serde(default)]
    clipboard: String,
    #[serde(default)]
    screenshot_path: String,
    #[serde(default)]
    screenshot_type: String,
    #[serde(default)]
    created_date: Option<String>,
    #[serde(default)]
    last_edited_date: Option<String>,
}

async fn api_capture(Form(f): Form<CaptureForm>) -> impl IntoResponse {
    let ts = chrono::Utc::now();
    let cds = f.created_date.clone().unwrap_or_else(|| ts.date_naive().to_string());
    let les = f.last_edited_date.clone().unwrap_or_else(|| ts.date_naive().to_string());

    let tag_list: Vec<String> = f.tags.split(',').map(|t| t.trim().to_string()).filter(|t| !t.is_empty()).collect();
    let src_list: Vec<String> = f.sources.split(',').map(|s| s.trim().to_string()).filter(|s| !s.is_empty()).collect();
    let mod_list: Vec<String> = {
        let v: Vec<String> = f.modalities.split(',').map(|m| m.trim().to_string()).filter(|m| !m.is_empty()).collect();
        if v.is_empty() { vec!["text".into()] } else { v }
    };
    let mut files_meta: Vec<serde_json::Value> = vec![];
    if !f.screenshot_path.is_empty() && !f.screenshot_type.is_empty() {
        files_meta.push(serde_json::json!({"path": f.screenshot_path, "type": f.screenshot_type}));
    }

    let capture = serde_json::json!({
        "timestamp": ts.to_rfc3339_opts(chrono::SecondsFormat::Secs, true),
        "content": f.content,
        "clipboard": f.clipboard,
        "context": f.context.trim(),
        "tags": tag_list,
        "modalities": mod_list,
        "sources": src_list,
        "location": serde_json::Value::Null,
        "media_files": files_meta,
        "created_date": cds,
        "last_edited_date": les,
    });

    let res = markdown::write_capture_with(capture.clone());
    db::store_capture_data(&capture);
    Json(serde_json::json!({ "saved_to": res.saved_to, "verified": res.verified }))
}

async fn api_suggestions(Path(field_type): Path<String>, Query(q): Query<HashMap<String, String>>) -> impl IntoResponse {
    if field_type != "tag" && field_type != "source" && field_type != "context" {
        return (StatusCode::BAD_REQUEST, Json(serde_json::json!({ "error": "Invalid field type" }))).into_response();
    }
    let query = q.get("query").cloned().unwrap_or_default();
    let limit = q.get("limit").and_then(|s| s.parse::<usize>().ok()).unwrap_or(10);
    let items = db::get_suggestions(&field_type, &query, limit);
    let suggestions: Vec<serde_json::Value> = items.into_iter().map(|s| {
        serde_json::json!({
            "value": s.value,
            "count": s.count,
            "last_used": s.last_used,
            "color": s.color
        })
    }).collect();
    Json(serde_json::json!({ "suggestions": suggestions })).into_response()
}

async fn api_suggestion_exists(Path(field_type): Path<String>, Query(q): Query<HashMap<String, String>>) -> impl IntoResponse {
    if field_type != "tag" && field_type != "source" && field_type != "context" {
        return (StatusCode::BAD_REQUEST, Json(serde_json::json!({ "error": "Invalid field type" }))).into_response();
    }
    let value = q.get("value").cloned().unwrap_or_default();
    let res = db::suggestion_exists(&field_type, &value);
    Json(res).into_response()
}

async fn api_recent_values() -> impl IntoResponse {
    let res = db::recent_values();
    Json(res)
}

async fn api_audio_start() -> impl IntoResponse {
    Json(serde_json::json!({ "status": "recording_started", "recorder_id": "stub" }))
}

async fn api_audio_stop() -> impl IntoResponse {
    Json(serde_json::json!({
        "status": "recording_saved",
        "filename": "audio_stub.wav",
        "filepath": ""
    }))
}

async fn api_audio_status(Path(recorder_id): Path<String>) -> impl IntoResponse {
    let _ = recorder_id;
    Json(serde_json::json!({
        "is_recording": false,
        "duration_seconds": 0.0,
        "samples_collected": 0
    }))
}

fn spawn_server() -> SocketAddr {
    let addr: SocketAddr = "127.0.0.1:14321".parse().unwrap();
    if SERVER_ADDR.get().is_some() {
        return *SERVER_ADDR.get().unwrap();
    }
    SERVER_ADDR.set(addr).ok();
    thread::spawn(move || {
        let rt = tokio::runtime::Runtime::new().unwrap();
        rt.block_on(async move {
            let cors = CorsLayer::new().allow_origin(Any).allow_methods(Any).allow_headers(Any);
            let app = Router::new()
                .route("/api/config", get(api_config))
                .route("/api/clipboard", get(api_clipboard))
                .route("/api/screenshot", post(api_screenshot))
                .route("/api/capture", post(api_capture))
                .route("/api/suggestions/:field_type", get(api_suggestions))
                .route("/api/suggestion-exists/:field_type", get(api_suggestion_exists))
                .route("/api/recent-values", get(api_recent_values))
                .route("/api/audio/start", post(api_audio_start))
                .route("/api/audio/stop", post(api_audio_stop))
                .route("/api/audio/status/:recorder_id", get(api_audio_status))
                .layer(cors);
            let listener = tokio::net::TcpListener::bind(addr).await.unwrap();
            axum::serve(listener, app.into_make_service())
                .await
                .unwrap();
        });
    });
    addr
}

#[tauri::command]
fn api_base() -> String {
    let addr = spawn_server();
    format!("http://{}", addr)
}

pub fn run() {
  let addr = spawn_server();

  tauri::Builder::default()
    .setup(move |app| {
      if let Some(win) = app.get_webview_window("main") {
        let js = format!("window.__KMS_API_BASE = 'http://{}';", addr);
        let _ = win.eval(&js);
      }
      Ok(())
    })
    .plugin(tauri_plugin_log::Builder::default().build())
    .invoke_handler(tauri::generate_handler![api_base])
    .run(tauri::generate_context!())
    .expect("error while running tauri application");
}

use tauri::Manager;
use std::{net::SocketAddr, thread};
use once_cell::sync::OnceCell;
use axum::{
    routing::{get, post},
    Router,
    response::IntoResponse,
    extract::{Path, Query},
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
    Json(serde_json::json!({ "content": "", "type": "text" }))
}

async fn api_screenshot() -> impl IntoResponse {
    Json(serde_json::json!({ "success": true, "path": "" }))
}

async fn api_capture() -> impl IntoResponse {
    let res = markdown::write_capture();
    Json(res)
}

async fn api_suggestions(Path(field_type): Path<String>, Query(q): Query<HashMap<String, String>>) -> impl IntoResponse {
    if field_type != "tag" && field_type != "source" && field_type != "context" {
        return (StatusCode::BAD_REQUEST, Json(serde_json::json!({ "error": "Invalid field type" }))).into_response();
    }
    let query = q.get("query").cloned().unwrap_or_default();
    let limit = q.get("limit").and_then(|s| s.parse::<usize>().ok()).unwrap_or(10);
    let res = db::get_suggestions(&field_type, &query, limit);
    Json(res).into_response()
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

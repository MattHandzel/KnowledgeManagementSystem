use tauri::Manager;
use std::{net::SocketAddr, thread};
use once_cell::sync::OnceCell;
use axum::{routing::get, Router, response::IntoResponse};
use tower_http::cors::{Any, CorsLayer};

static SERVER_ADDR: OnceCell<SocketAddr> = OnceCell::new();

async fn api_config() -> impl IntoResponse {
    let json = serde_json::json!({
        "vault": { "path": "", "capture_dir": "", "media_dir": "" },
        "ui": { "clipboard_poll_ms": 200 },
        "is_dev": true
    });
    axum::Json(json)
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

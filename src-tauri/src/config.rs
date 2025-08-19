use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct VaultConfig {
    pub path: String,
    pub capture_dir: String,
    pub media_dir: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct UiConfig {
    pub clipboard_poll_ms: u64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AppConfig {
    pub vault: VaultConfig,
    pub ui: UiConfig,
    pub is_dev: bool,
}

pub fn load_config() -> AppConfig {
    AppConfig {
        vault: VaultConfig {
            path: String::new(),
            capture_dir: String::new(),
            media_dir: String::new(),
        },
        ui: UiConfig {
            clipboard_poll_ms: 200,
        },
        is_dev: cfg!(debug_assertions),
    }
}

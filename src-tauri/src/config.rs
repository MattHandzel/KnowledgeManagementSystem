use serde::{Deserialize, Serialize};
use std::{env, fs, path::{Path, PathBuf}};

#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub struct VaultConfig {
    pub path: String,
    pub capture_dir: String,
    pub media_dir: String,
}

#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub struct UiConfig {
    pub clipboard_poll_ms: Option<u64>,
}

#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub struct DatabaseConfig {
    pub path: String,
}

#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub struct AppConfig {
    pub vault: VaultConfig,
    pub database: DatabaseConfig,
    pub ui: UiConfig,
    pub capture: serde_yaml::Value,
    pub keybindings: serde_yaml::Value,
    pub theme: serde_yaml::Value,
    pub mode: String,
    pub is_dev: bool,
}

#[derive(Debug, Clone, Deserialize, Default)]
struct RawConfig {
    vault: Option<serde_yaml::Value>,
    database: Option<serde_yaml::Value>,
    ui: Option<serde_yaml::Value>,
    capture: Option<serde_yaml::Value>,
    keybindings: Option<serde_yaml::Value>,
    theme: Option<serde_yaml::Value>,
    development: Option<serde_yaml::Value>,
}

fn repo_root() -> PathBuf {
    let mut p = env::current_dir().unwrap_or_else(|_| PathBuf::from("."));
    if let Ok(cfg) = env::var("KMS_CONFIG_PATH") {
        return PathBuf::from(cfg).parent().unwrap_or_else(|| Path::new(".")).to_path_buf();
    }
    for _ in 0..4 {
        let try_cfg = p.join("config.yaml");
        if try_cfg.exists() {
            return p;
        }
        if !p.pop() {
            break;
        }
    }
    p
}

fn load_yaml_config() -> RawConfig {
    if let Ok(cfg_path) = env::var("KMS_CONFIG_PATH") {
        let path = PathBuf::from(cfg_path);
        if let Ok(s) = fs::read_to_string(&path) {
            if let Ok(rc) = serde_yaml::from_str::<RawConfig>(&s) {
                return rc;
            }
        }
    }
    let path = repo_root().join("config.yaml");
    if let Ok(s) = fs::read_to_string(&path) {
        if let Ok(rc) = serde_yaml::from_str::<RawConfig>(&s) {
            return rc;
        }
    }
    RawConfig::default()
}

pub fn load_config() -> AppConfig {
    let raw = load_yaml_config();

    let dev_mode = raw
        .development
        .as_ref()
        .and_then(|v| v.get("mode"))
        .and_then(|m| m.as_str().map(|s| s.to_string()))
        .unwrap_or_else(|| "prod".to_string());
    let is_dev = dev_mode == "dev";

    let mut vault_path = raw
        .vault
        .as_ref()
        .and_then(|v| v.get("path"))
        .and_then(|p| p.as_str())
        .map(|s| s.to_string())
        .unwrap_or_else(|| "~/notes".to_string());

    if vault_path == "ROOT_DIRECTORY_PATH" {
        vault_path = repo_root().to_string_lossy().to_string();
    } else if vault_path == "ROOT_DIRECTORY_PATH/dev" {
        vault_path = repo_root().join("dev").to_string_lossy().to_string();
    }

    if let Ok(env_vault) = env::var("KMS_VAULT_PATH") {
        vault_path = env_vault;
    }

    let capture_dir = raw
        .vault
        .as_ref()
        .and_then(|v| v.get("capture_dir"))
        .and_then(|p| p.as_str())
        .unwrap_or("capture/raw_capture")
        .to_string();
    let media_dir = raw
        .vault
        .as_ref()
        .and_then(|v| v.get("media_dir"))
        .and_then(|p| p.as_str())
        .unwrap_or("capture/raw_capture/media")
        .to_string();

    let mut db_path = raw
        .database
        .as_ref()
        .and_then(|d| d.get("path"))
        .and_then(|p| p.as_str())
        .unwrap_or("server/main.db")
        .to_string();

    if let Ok(data_dir) = env::var("KMS_DATA_DIR") {
        db_path = PathBuf::from(data_dir)
            .join("main.db")
            .to_string_lossy()
            .to_string();
    } else if let Ok(env_db) = env::var("KMS_DB_PATH") {
        db_path = env_db;
    } else {
        let db_is_abs = PathBuf::from(&db_path).is_absolute();
        if !db_is_abs {
            if dev_mode == "prod" {
                let dir = if let Ok(xdg) = env::var("XDG_DATA_HOME") {
                    PathBuf::from(xdg).join("kms-capture")
                } else {
                    directories::BaseDirs::new()
                        .map(|b| b.home_dir().to_path_buf())
                        .unwrap_or_else(|| PathBuf::from("~"))
                        .join(".local/share/kms-capture")
                };
                let _ = fs::create_dir_all(&dir);
                db_path = dir.join("main.db").to_string_lossy().to_string();
            } else {
                db_path = repo_root().join(&db_path).to_string_lossy().to_string();
            }
        }
    }

    AppConfig {
        vault: VaultConfig {
            path: shellexpand::tilde(&vault_path).to_string(),
            capture_dir,
            media_dir,
        },
        database: DatabaseConfig { path: db_path },
        ui: match raw.ui.clone() {
            Some(v) => serde_yaml::from_value(v).unwrap_or_default(),
            None => UiConfig::default(),
        },
        capture: raw.capture.unwrap_or_else(|| serde_yaml::Value::Mapping(Default::default())),
        keybindings: raw.keybindings.unwrap_or_else(|| serde_yaml::Value::Mapping(Default::default())),
        theme: raw.theme.unwrap_or_else(|| serde_yaml::Value::Mapping(Default::default())),
        mode: dev_mode,
        is_dev,
    }
}

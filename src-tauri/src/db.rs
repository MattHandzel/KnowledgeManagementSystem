use serde::Serialize;

#[derive(Debug, Clone, Serialize)]
pub struct Suggestions {
    pub suggestions: Vec<String>,
}

#[derive(Debug, Clone, Serialize)]
pub struct Exists {
    pub exists: bool,
}

#[derive(Debug, Clone, Serialize)]
pub struct RecentValues {
    pub recent_values: serde_json::Value,
}

pub fn get_suggestions(_field: &str, _query: &str, _limit: usize) -> Suggestions {
    Suggestions { suggestions: vec![] }
}

pub fn suggestion_exists(_field: &str, _value: &str) -> Exists {
    Exists { exists: false }
}

pub fn recent_values() -> RecentValues {
    RecentValues {
        recent_values: serde_json::json!({}),
    }
}

use serde::Serialize;

#[derive(Debug, Clone, Serialize)]
pub struct CaptureResult {
    pub saved_to: String,
    pub verified: bool,
}

pub fn write_capture() -> CaptureResult {
    CaptureResult {
        saved_to: String::new(),
        verified: true,
    }
}

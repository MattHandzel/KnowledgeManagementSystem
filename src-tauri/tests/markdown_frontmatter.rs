use app_lib::markdown::write_capture_with;
use serde_json::json;

#[test]
fn frontmatter_has_no_extra_newline_and_importance_defaults_null() {
    let tempdir = tempfile::tempdir().expect("tempdir");
    std::env::set_var("KMS_VAULT_PATH", tempdir.path().to_string_lossy().to_string());

    let capture = json!({
        "content": "Hello world",
        "tags": ["test"],
        "sources": ["manual"],
        "modalities": ["text"],
        "metadata": {},
    });

    let res = write_capture_with(capture);
    assert!(res.verified);
    assert!(res.saved_to.ends_with(".md"));
    let content = std::fs::read_to_string(&res.saved_to).expect("file read");
    assert!(content.contains("\n---\n"), "frontmatter boundary missing");
    assert!(!content.contains("importance: 0.5"));
}

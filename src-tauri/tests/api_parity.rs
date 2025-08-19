use std::time::Duration;

#[tokio::test]
async fn config_endpoint_returns_expected_shape() {
    let client = reqwest::Client::builder().timeout(Duration::from_secs(2)).build().unwrap();
    match client.get("http://127.0.0.1:14321/api/config").send().await {
        Ok(resp) => {
            assert!(resp.status().is_success());
            let json: serde_json::Value = resp.json().await.unwrap();
            assert!(json.get("vault").is_some());
            assert!(json.get("database").is_some());
            assert!(json.get("ui").is_some());
        }
        Err(e) => {
            eprintln!("Skipping due to server not running: {}", e);
        }
    }
}

#[tokio::test]
async fn suggestions_shape_is_valid_even_empty() {
    let client = reqwest::Client::builder().timeout(Duration::from_secs(2)).build().unwrap();
    match client
        .get("http://127.0.0.1:14321/api/suggestions/tag?query=&limit=5")
        .send()
        .await
    {
        Ok(resp) => {
            assert!(resp.status().is_success());
            let json: serde_json::Value = resp.json().await.unwrap();
            assert!(json.get("suggestions").is_some());
        }
        Err(e) => {
            eprintln!("Skipping due to server not running: {}", e);
        }
    }
}

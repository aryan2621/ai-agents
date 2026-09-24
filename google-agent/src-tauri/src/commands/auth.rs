use std::time::Duration;

use tauri::command;
use tauri::{AppHandle, Manager};
use tauri_plugin_opener::OpenerExt;

const BACKEND_AUTH_URL: &str = "http://127.0.0.1:8000/auth/google/url";
const OAUTH_BEGIN_URL: &str = "http://127.0.0.1:8000/auth/google/begin";
const OAUTH_REDIRECT_URI: &str = "http://127.0.0.1:8000/auth/google/callback";
const BACKEND_STARTUP_ATTEMPTS: u32 = 120;
const BACKEND_RETRY_DELAY_MS: u64 = 500;

struct AuthStart {
    state: String,
}

async fn fetch_google_auth_start(client: &reqwest::Client) -> Result<AuthStart, String> {
    for attempt in 0..BACKEND_STARTUP_ATTEMPTS {
        match client.get(BACKEND_AUTH_URL).send().await {
            Ok(response) if response.status().is_success() => {
                let body: serde_json::Value = response.json().await.map_err(|e| e.to_string())?;
                let state = body
                    .get("state")
                    .and_then(|v| v.as_str())
                    .ok_or_else(|| "Backend did not return OAuth state".to_string())?
                    .to_string();
                return Ok(AuthStart { state });
            }
            Ok(response) => {
                let status = response.status();
                let body = response.text().await.unwrap_or_default();
                return Err(format!(
                    "Backend auth URL request failed ({}): {}",
                    status, body
                ));
            }
            Err(_) if attempt + 1 < BACKEND_STARTUP_ATTEMPTS => {
                tokio::time::sleep(Duration::from_millis(BACKEND_RETRY_DELAY_MS)).await;
            }
            Err(e) => {
                return Err(format!(
                    "Failed to reach backend after {}s: {}",
                    (BACKEND_STARTUP_ATTEMPTS as u64 * BACKEND_RETRY_DELAY_MS) / 1000,
                    e
                ));
            }
        }
    }

    Err("Backend did not become ready in time".to_string())
}

fn preferred_oauth_browser() -> Option<String> {
    std::env::var("OAUTH_BROWSER")
        .ok()
        .filter(|v| !v.trim().is_empty())
        .or_else(|| {
            #[cfg(target_os = "macos")]
            {
                Some("Brave Browser".to_string())
            }
            #[cfg(not(target_os = "macos"))]
            {
                None
            }
        })
}

fn open_auth_url(app: &AppHandle, url: &str) -> Result<(), String> {
    if let Some(browser) = preferred_oauth_browser() {
        if app.opener().open_url(url, Some(browser.as_str())).is_ok() {
            return Ok(());
        }
    }

    app.opener()
        .open_url(url, None::<&str>)
        .map_err(|e| e.to_string())
}

#[command]
pub async fn start_google_auth(app: tauri::AppHandle) -> Result<String, String> {
    let client = reqwest::Client::new();
    let auth_start = fetch_google_auth_start(&client).await?;

    let begin_url = format!(
        "{}?state={}",
        OAUTH_BEGIN_URL,
        urlencoding::encode(&auth_start.state)
    );
    open_auth_url(&app, &begin_url)?;

    Ok(auth_start.state)
}

#[command]
pub async fn handle_oauth_callback(code: String) -> Result<serde_json::Value, String> {
    let client = reqwest::Client::new();
    let response = client
        .post("http://127.0.0.1:8000/auth/google/callback")
        .json(&serde_json::json!({
            "code": code,
            "redirect_uri": OAUTH_REDIRECT_URI
        }))
        .send()
        .await
        .map_err(|e| e.to_string())?;

    if !response.status().is_success() {
        let status = response.status();
        let body = response.text().await.unwrap_or_default();
        return Err(format!("Token exchange failed ({}): {}", status, body));
    }

    let tokens: serde_json::Value = response.json().await.map_err(|e| e.to_string())?;
    Ok(tokens)
}

#[command]
pub async fn focus_main_window(app: tauri::AppHandle) -> Result<(), String> {
    if let Some(window) = app.get_webview_window("main") {
        window.unminimize().map_err(|e| e.to_string())?;
        window.show().map_err(|e| e.to_string())?;
        window.set_focus().map_err(|e| e.to_string())?;
    }
    Ok(())
}

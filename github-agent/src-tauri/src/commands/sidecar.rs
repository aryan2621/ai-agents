use std::collections::HashMap;
use std::fs;
use std::path::{Path, PathBuf};
use std::sync::Mutex;
use std::time::Duration;

use tauri::command;
use tauri::Emitter;
use tauri_plugin_shell::process::CommandChild;
use tauri_plugin_shell::ShellExt;

static SIDECAR_CHILD: Mutex<Option<CommandChild>> = Mutex::new(None);

fn backend_env_candidates() -> Vec<PathBuf> {
    let manifest = PathBuf::from(env!("CARGO_MANIFEST_DIR"));
    vec![
        manifest.join("binaries/.env"),
        manifest.join("../backend/.env"),
    ]
}

fn parse_env_file(path: &Path) -> HashMap<String, String> {
    let content = fs::read_to_string(path).unwrap_or_default();
    let mut map = HashMap::new();
    for line in content.lines() {
        let line = line.trim();
        if line.is_empty() || line.starts_with('#') {
            continue;
        }
        if let Some((key, value)) = line.split_once('=') {
            let value = value.trim().trim_matches('"').trim_matches('\'');
            map.insert(key.trim().to_string(), value.to_string());
        }
    }
    map
}

fn load_backend_env() -> HashMap<String, String> {
    let mut merged = HashMap::new();
    for path in backend_env_candidates() {
        if path.is_file() {
            merged.extend(parse_env_file(&path));
        }
    }
    merged
}

pub async fn backend_is_healthy() -> bool {
    let client = reqwest::Client::new();
    match client.get("http://127.0.0.1:8000/health").send().await {
        Ok(response) => response.status().is_success(),
        Err(_) => false,
    }
}

fn capabilities_include(body: &serde_json::Value, name: &str) -> bool {
    body.get("capabilities")
        .and_then(|value| value.as_array())
        .map(|items| {
            items
                .iter()
                .filter_map(|item| item.as_str())
                .any(|cap| cap == name)
        })
        .unwrap_or(false)
}

async fn backend_has_ollama_stack() -> bool {
    let client = reqwest::Client::new();
    let response = match client.get("http://127.0.0.1:8000/health").send().await {
        Ok(response) if response.status().is_success() => response,
        _ => return false,
    };

    let body: serde_json::Value = match response.json().await {
        Ok(body) => body,
        Err(_) => return false,
    };

    let build_id = body.get("build_id").and_then(|value| value.as_str()).unwrap_or("");
    capabilities_include(&body, "ollama")
        && !capabilities_include(&body, "gemini")
        && !capabilities_include(&body, "groq")
        && (build_id.is_empty() || build_id == "ollama-only-v8")
}

async fn backend_is_current() -> bool {
    backend_has_ollama_stack().await
}

async fn kill_process_on_port_8000() {
    #[cfg(unix)]
    {
        let _ = tokio::process::Command::new("sh")
            .arg("-c")
            .arg("lsof -ti :8000 | xargs kill -9 2>/dev/null || true")
            .output()
            .await;
        tokio::time::sleep(Duration::from_millis(700)).await;
    }
}

pub async fn start_python_backend_internal(app: &tauri::AppHandle) {
    if backend_is_healthy().await {
        if backend_is_current().await {
            eprintln!(
                "[github-agent] Backend already running on http://127.0.0.1:8000 — skipping sidecar spawn"
            );
            let _ = app.emit("backend-ready", ());
            return;
        }

        eprintln!(
            "[github-agent] Stale backend on http://127.0.0.1:8000 (missing Ollama-only stack) — restarting sidecar. Run: npm run build:sidecar"
        );
        kill_process_on_port_8000().await;
    }

    let mut sidecar_command = match app.shell().sidecar("python-backend") {
        Ok(cmd) => cmd,
        Err(e) => {
            let _ = app.emit(
                "backend-error",
                format!("Failed to create sidecar: {}. Run npm run build:sidecar", e),
            );
            return;
        }
    };

    for (key, value) in load_backend_env() {
        sidecar_command = sidecar_command.env(key, value);
    }

    let (mut rx, child) = match sidecar_command.spawn() {
        Ok(pair) => pair,
        Err(e) => {
            let _ = app.emit("backend-error", format!("Failed to spawn python backend: {}", e));
            return;
        }
    };

    if let Ok(mut guard) = SIDECAR_CHILD.lock() {
        *guard = Some(child);
    }

    let app_for_ready = app.clone();
    tokio::spawn(async move {
        for _ in 0..120 {
            if backend_is_healthy().await && backend_is_current().await {
                let _ = app_for_ready.emit("backend-ready", ());
                break;
            }
            tokio::time::sleep(Duration::from_millis(500)).await;
        }
    });

    let app_handle = app.clone();
    while let Some(event) = rx.recv().await {
        match event {
            tauri_plugin_shell::process::CommandEvent::Stdout(line) => {
                let message = String::from_utf8_lossy(&line).to_string();
                #[cfg(debug_assertions)]
                eprintln!("[backend] {}", message.trim_end());
                let _ = app_handle.emit("backend-log", message);
            }
            tauri_plugin_shell::process::CommandEvent::Stderr(line) => {
                let message = String::from_utf8_lossy(&line).to_string();
                #[cfg(debug_assertions)]
                eprintln!("[backend:err] {}", message.trim_end());
                let _ = app_handle.emit("backend-error", message);
            }
            tauri_plugin_shell::process::CommandEvent::Terminated(payload) => {
                let _ = app_handle.emit(
                    "backend-log",
                    format!("Backend terminated with code: {:?}", payload.code),
                );
                break;
            }
            _ => {}
        }
    }
}

pub async fn stop_python_backend_internal(_app: &tauri::AppHandle) {
    if let Ok(mut guard) = SIDECAR_CHILD.lock() {
        if let Some(child) = guard.take() {
            let _ = child.kill();
        }
    }
}

#[command]
pub async fn start_python_backend(app: tauri::AppHandle) -> Result<(), String> {
    start_python_backend_internal(&app).await;
    Ok(())
}

#[command]
pub async fn stop_python_backend(app: tauri::AppHandle) -> Result<(), String> {
    stop_python_backend_internal(&app).await;
    Ok(())
}

#[command]
pub async fn check_backend_health() -> Result<bool, String> {
    Ok(backend_is_healthy().await)
}

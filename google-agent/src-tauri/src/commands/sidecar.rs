use std::collections::HashMap;
use std::fs;
use std::path::{Path, PathBuf};
use std::sync::Mutex;
use std::time::Duration;

use tauri::command;
use tauri::Emitter;
use tauri::Manager;
use tauri_plugin_shell::process::CommandChild;
use tauri_plugin_shell::ShellExt;

/// The backend's port, from ports.json (see build.rs).
const BACKEND_PORT: &str = env!("BACKEND_PORT");
const BACKEND_ADDR: &str = concat!("127.0.0.1:", env!("BACKEND_PORT"));

static SIDECAR_CHILD: Mutex<Option<CommandChild>> = Mutex::new(None);
/// Set while the app quits, so a backend that exits then isn't restarted.
static STOPPING: std::sync::atomic::AtomicBool = std::sync::atomic::AtomicBool::new(false);

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

/// The OAuth client, read from the build environment at compile time: release builds get
/// GOOGLE_AGENT_CLIENT_ID/_SECRET from the repository's Actions secrets. A local `backend/.env`
/// still takes precedence.
const BUILD_ENV: [(&str, Option<&str>); 2] = [
    ("GOOGLE_CLIENT_ID", option_env!("GOOGLE_AGENT_CLIENT_ID")),
    ("GOOGLE_CLIENT_SECRET", option_env!("GOOGLE_AGENT_CLIENT_SECRET")),
];

fn load_backend_env() -> HashMap<String, String> {
    let mut merged = HashMap::new();
    for path in backend_env_candidates() {
        if path.is_file() {
            merged.extend(parse_env_file(&path));
        }
    }
    for (key, value) in BUILD_ENV {
        if let Some(value) = value.filter(|v| !v.is_empty()) {
            merged.entry(key.to_string()).or_insert_with(|| value.to_string());
        }
    }
    merged
}

pub async fn backend_is_healthy() -> bool {
    let client = reqwest::Client::new();
    match client.get(format!("http://{BACKEND_ADDR}/health")).send().await {
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

/// The backend this build ships: built-in llama.cpp AI and local JSON storage.
async fn backend_has_builtin_llm() -> bool {
    let client = reqwest::Client::new();
    let response = match client.get(format!("http://{BACKEND_ADDR}/health")).send().await {
        Ok(response) if response.status().is_success() => response,
        _ => return false,
    };

    let body: serde_json::Value = match response.json().await {
        Ok(body) => body,
        Err(_) => return false,
    };

    let build_id = body.get("build_id").and_then(|value| value.as_str()).unwrap_or("");
    capabilities_include(&body, "llama.cpp") && build_id == "builtin-llm-v1"
}

async fn backend_is_current() -> bool {
    backend_has_builtin_llm().await
}

/// Stops a backend of this app that holds the port (one left from an earlier launch, or an older
/// build). Only ours — matched by command line — never another program that happens to use it.
async fn stop_own_backend_on_port() {
    #[cfg(unix)]
    {
        let script = format!(
            "for p in $(lsof -ti tcp:{BACKEND_PORT} -sTCP:LISTEN); do \
            case \"$(ps -o command= -p $p)\" in *python-backend*|*uvicorn*app.main*) kill $p;; esac; done"
        );
        let _ = tokio::process::Command::new("sh").arg("-c").arg(script).output().await;
        tokio::time::sleep(Duration::from_millis(1500)).await;
    }
}

/// The name of the program listening on the backend port, if any.
async fn port_holder() -> Option<String> {
    let output = tokio::process::Command::new("lsof")
        .args(["-nP", &format!("-iTCP:{BACKEND_PORT}"), "-sTCP:LISTEN", "-Fc"])
        .output()
        .await
        .ok()?;
    String::from_utf8_lossy(&output.stdout)
        .lines()
        .find_map(|line| line.strip_prefix('c').map(str::to_string))
}

pub async fn start_python_backend_internal(app: &tauri::AppHandle) {
    // If the backend stops unexpectedly, start it again (a few times, then give up and let the
    // app show "Backend is not running").
    for attempt in 0..3 {
        if !run_backend(app).await || STOPPING.load(std::sync::atomic::Ordering::SeqCst) {
            return;
        }
        eprintln!("[google-agent] Backend stopped unexpectedly — restarting (attempt {})", attempt + 1);
        tokio::time::sleep(Duration::from_secs(1)).await;
    }
}

/// Runs one backend until it exits. Returns false if none was started (one is already running
/// or it could not be spawned).
async fn run_backend(app: &tauri::AppHandle) -> bool {
    if backend_is_healthy().await && backend_is_current().await {
        eprintln!("[google-agent] Backend already running on http://{BACKEND_ADDR} — skipping sidecar spawn");
        let _ = app.emit("backend-ready", ());
        return false;
    }

    // The backend port is taken but not answering: a backend from an earlier launch may still be
    // unpacking itself. Give it a moment before replacing it, or the new one can't bind the port.
    if std::net::TcpListener::bind(BACKEND_ADDR).is_err() {
        for _ in 0..30 {
            tokio::time::sleep(Duration::from_millis(500)).await;
            if backend_is_healthy().await && backend_is_current().await {
                let _ = app.emit("backend-ready", ());
                return false;
            }
        }
        eprintln!("[google-agent] Port {BACKEND_PORT} is held by an unresponsive or outdated backend — replacing it");
        stop_own_backend_on_port().await;
        if std::net::TcpListener::bind(BACKEND_ADDR).is_err() {
            let holder = port_holder().await.unwrap_or_else(|| "another program".to_string());
            let _ = app.emit(
                "backend-error",
                format!("Port {BACKEND_PORT} is in use by {holder}. Quit it, then reopen Google Agent."),
            );
            return false;
        }
    }

    // The backend ships unpacked in Resources/python-backend/ (a PyInstaller folder build).
    let exe = match app.path().resource_dir() {
        Ok(dir) => dir.join("python-backend").join("python-backend"),
        Err(e) => {
            let _ = app.emit("backend-error", format!("Cannot find app resources: {}", e));
            return false;
        }
    };
    let mut sidecar_command = app.shell().command(exe);

    for (key, value) in load_backend_env() {
        sidecar_command = sidecar_command.env(key, value);
    }
    // The bundled llama.cpp server (externalBin) sits next to this app's executable.
    if let Some(dir) = std::env::current_exe().ok().and_then(|p| p.parent().map(|d| d.to_path_buf())) {
        sidecar_command = sidecar_command.env("LLAMA_SERVER_PATH", dir.join("llama-server"));
    }

    let (mut rx, child) = match sidecar_command.spawn() {
        Ok(pair) => pair,
        Err(e) => {
            let _ = app.emit("backend-error", format!("Failed to spawn python backend: {}", e));
            return false;
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
    true
}

pub async fn stop_python_backend_internal(_app: &tauri::AppHandle) {
    STOPPING.store(true, std::sync::atomic::Ordering::SeqCst);
    // Only our own child (killing whatever holds the port could take down another instance's
    // backend). Ask it to stop first: a graceful shutdown also stops its AI model server, which a
    // plain kill would leave running.
    let child = SIDECAR_CHILD.lock().ok().and_then(|mut guard| guard.take());
    let Some(child) = child else { return };
    #[cfg(unix)]
    {
        let pid = child.pid().to_string();
        let _ = std::process::Command::new("kill").args(["-TERM", &pid]).status();
        for _ in 0..30 {
            let alive = std::process::Command::new("kill")
                .args(["-0", &pid])
                .status()
                .map(|s| s.success())
                .unwrap_or(false);
            if !alive {
                return;
            }
            tokio::time::sleep(Duration::from_millis(100)).await;
        }
    }
    let _ = child.kill();
}

#[command]
pub async fn check_backend_health() -> Result<bool, String> {
    Ok(backend_is_healthy().await)
}

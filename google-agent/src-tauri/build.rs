fn main() {
    // Rebuild when the OAuth client baked in by commands/sidecar.rs changes.
    println!("cargo:rerun-if-env-changed=GOOGLE_AGENT_CLIENT_ID");
    println!("cargo:rerun-if-env-changed=GOOGLE_AGENT_CLIENT_SECRET");
    // ports.json is the one place the ports are set; the code reads BACKEND_PORT from it.
    println!("cargo:rerun-if-changed=../ports.json");
    println!("cargo:rerun-if-changed=tauri.conf.json");
    let ports = std::fs::read_to_string("../ports.json").expect("read ../ports.json");
    let port = |name: &str| {
        ports
            .split(&format!("\"{name}\""))
            .nth(1)
            .and_then(|rest| rest.split(|c: char| !c.is_ascii_digit()).find(|t| !t.is_empty()))
            .unwrap_or_else(|| panic!("ports.json has no \"{name}\" port"))
            .to_string()
    };
    let (backend, ui) = (port("backend"), port("ui"));
    println!("cargo:rustc-env=BACKEND_PORT={backend}");
    // tauri.conf.json is static JSON, so it can't read ports.json: fail the build if it drifts.
    let conf = std::fs::read_to_string("tauri.conf.json").expect("read tauri.conf.json");
    assert!(
        conf.contains(&format!("http://127.0.0.1:{backend} ")),
        "tauri.conf.json CSP must allow http://127.0.0.1:{backend} (the backend port in ports.json)"
    );
    assert!(
        conf.contains(&format!("\"devUrl\": \"http://localhost:{ui}\"")),
        "tauri.conf.json devUrl must be http://localhost:{ui} (the ui port in ports.json)"
    );
    tauri_build::build()
}

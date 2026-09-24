pub mod commands;

#[cfg(all(desktop, any(target_os = "linux", target_os = "windows")))]
use tauri_plugin_deep_link::DeepLinkExt;

pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_store::Builder::default().build())
        .plugin(tauri_plugin_shell::init())
        .plugin(tauri_plugin_opener::init())
        .plugin(tauri_plugin_deep_link::init())
        .plugin(tauri_plugin_global_shortcut::Builder::new().build())
        .invoke_handler(tauri::generate_handler![
            commands::auth::start_github_auth,
            commands::auth::handle_oauth_callback,
            commands::auth::focus_main_window,
            commands::sidecar::start_python_backend,
            commands::sidecar::stop_python_backend,
            commands::sidecar::check_backend_health,
        ])
        .setup(|app| {
            #[cfg(all(desktop, any(target_os = "linux", target_os = "windows")))]
            app.deep_link().register("github-agent")?;

            if let Err(err) = commands::tray::setup_tray(app) {
                eprintln!("tray setup failed: {err}");
            }
            commands::tray::setup_global_shortcut(app.handle());

            let handle = app.handle().clone();
            tauri::async_runtime::spawn(async move {
                commands::sidecar::start_python_backend_internal(&handle).await;
            });

            Ok(())
        })
        .build(tauri::generate_context!())
        .expect("error while building tauri application")
        .run(|app_handle, event| {
            if let tauri::RunEvent::Exit = event {
                let handle = app_handle.clone();
                tauri::async_runtime::block_on(async move {
                    commands::sidecar::stop_python_backend_internal(&handle).await;
                });
            }
        });
}

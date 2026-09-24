export async function focusAppWindow() {
  try {
    const { getCurrentWindow } = await import('@tauri-apps/api/window')
    const win = getCurrentWindow()
    await win.unminimize()
    await win.show()
    await win.setFocus()
  } catch {
    // Not running inside Tauri (e.g. web-only dev)
  }
}

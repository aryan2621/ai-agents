#!/usr/bin/env bash
# Starts the app in dev mode. The UI dev server runs on $GITHUB_AGENT_UI_PORT, or the "ui" port in
# ports.json (no other desktop app here uses it); the backend uses the "backend" port there.
# Fails if the UI port is taken, rather than letting Next pick another one the window
# wouldn't load.
set -euo pipefail
cd "$(dirname "$0")/.."

export GITHUB_AGENT_UI_PORT="${GITHUB_AGENT_UI_PORT:-$(node -p "require('./ports.json').ui")}"
if lsof -nP -iTCP:"$GITHUB_AGENT_UI_PORT" -sTCP:LISTEN >/dev/null 2>&1; then
  echo "Port $GITHUB_AGENT_UI_PORT is already in use:" >&2
  lsof -nP -iTCP:"$GITHUB_AGENT_UI_PORT" -sTCP:LISTEN >&2
  echo "Stop that process, or set GITHUB_AGENT_UI_PORT to a free port." >&2
  exit 1
fi

exec npx tauri dev --config "{\"build\":{\"devUrl\":\"http://localhost:$GITHUB_AGENT_UI_PORT\"}}"

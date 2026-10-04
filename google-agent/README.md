# Google Agent

> **Just want to use the app?** See the [install guide](../README.md): download, opening an unsigned
> app, first-run setup and privacy. This page is for building from source.

A desktop AI assistant for Google Workspace (Gmail, Calendar, Drive, Docs, Sheets). Built with Tauri, Next.js, FastAPI and a built-in llama.cpp model. Chats are saved as local JSON files.

**Tagline:** Your private, local AI for Google Workspace — Gmail, Calendar, Drive, Docs, and Sheets.

## Prerequisites

1. **Node.js 20+** and **Rust** (for Tauri)
2. **Python 3.11+**
3. **CMake** (to build the bundled llama.cpp server; `brew install cmake`)
4. **Google Cloud OAuth** — create a **Desktop app** OAuth client in [Google Cloud Console](https://console.cloud.google.com/apis/credentials), and enable the Gmail, Calendar, Drive, Docs, and Sheets APIs. Add redirect URI:
   ```
   http://127.0.0.1:47832/auth/google/callback
   ```

### Ports

| | Google Agent | GitHub Agent |
|---|---|---|
| Backend (FastAPI) | 47832, fixed | 47831, fixed |
| Dev UI (`next dev`) | 47822, `GOOGLE_AGENT_UI_PORT` | 47821, `GITHUB_AGENT_UI_PORT` |
| llama-server | a free port picked at launch | same |

The two apps never share a port, so both can run at the same time. The backend port is fixed because
the OAuth redirect URI, the Tauri shell and the window's CSP all name it; it does not read `HOST` or
`PORT`. In dev, set `GOOGLE_AGENT_UI_PORT` to move the UI; `npm run dev` stops with a message if the
port is taken.

## Setup

1. Copy environment file:
   ```bash
   cp backend/.env.example backend/.env
   ```
2. Edit `backend/.env` with your Google OAuth credentials:
   ```
   GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
   GOOGLE_CLIENT_SECRET=your-client-secret
   ```
   In dev the app reads this file directly. Release builds ship without an OAuth client: on first
   run, the app asks each person for their own (Settings → Google OAuth, also shown at sign-in).
3. Install dependencies:
   ```bash
   npm install
   cd backend && pip install -r requirements.txt
   ```
4. On first launch, download a model in the onboarding step (or Settings → Models). It runs on this Mac;
   nothing else to install. A model already downloaded by GitHub Agent or Relay is reused. Chats, settings
   and models live in `~/Library/Application Support/Google Agent/` (override with `GOOGLE_AGENT_DATA_DIR`).

## Run

Desktop app only — the Python backend starts automatically as a bundled sidecar. No separate server terminal.

```bash
npm run dev
```

First run builds the sidecar binary if missing (~1–2 min). After that, startup is fast.

Rebuild the backend after Python changes:

```bash
npm run build:sidecar
```

## Production build

Builds the llama.cpp server, Next.js static export, PyInstaller sidecar, and Tauri app:

```bash
npm run build
```

Nothing secret is built in: release apps ask for the user's own Google OAuth client on first run and keep it
in the app's data folder on their Mac.

## Architecture

| Layer | Tech |
|-------|------|
| Shell | Tauri 2 (Rust) |
| UI | Next.js 14 static export |
| Backend | FastAPI sidecar on `127.0.0.1:47832` |
| LLM | Bundled llama.cpp server (`llama-server`) with open GGUF models |
| Storage | JSON files in the app's data folder |

Global shortcut: `Cmd+Shift+G` (macOS) / `Ctrl+Shift+G` (Windows/Linux).

## Scripts

| Command | Description |
|---------|-------------|
| `npm run dev` | Desktop app (auto-starts bundled backend) |
| `npm run build:sidecar` | Rebuild Python backend binary |
| `npm run build` | Full release build (.dmg / .app) |

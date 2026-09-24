# Google Agent

A desktop AI assistant for Google Workspace (Gmail, Calendar, Drive, Docs, Sheets). Built with Tauri, Next.js, FastAPI, local Ollama, and embedded SQLite.

**Tagline:** Your Google Workspace assistant — Gmail, Calendar, Drive, Docs, and Sheets.

## Prerequisites

1. **Node.js 20+** and **Rust** (for Tauri)
2. **Python 3.11+**
3. **PostgreSQL** (optional) — embedded **SQLite** is used by default; no database setup required
4. **Ollama** — install from [ollama.com](https://ollama.com), then pull the default model: `ollama pull qwen2.5:7b`
5. **Google Cloud OAuth** — create a **Desktop app** OAuth client in [Google Cloud Console](https://console.cloud.google.com/). Add redirect URI:
   ```
   http://127.0.0.1:8000/auth/google/callback
   ```

## Setup

1. Copy environment file:
   ```bash
   cp backend/.env.example backend/.env
   ```
2. Edit `backend/.env` with your Google OAuth credentials:
   ```
   GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
   GOOGLE_CLIENT_SECRET=your-client-secret
   DEFAULT_MODEL=qwen2.5:7b
   OLLAMA_BASE_URL=http://127.0.0.1:11434
   ```
   Copy it for the bundled backend:
   ```bash
   cp backend/.env src-tauri/binaries/.env
   ```
3. Install dependencies:
   ```bash
   npm install
   cd backend && pip install -r requirements.txt
   ```
4. Apply database migrations (first time, or after pulling schema changes):
   ```bash
   npm run db:migrate
   ```
   If the database was already created by the app (`init_db`) and migrate fails with "relation already exists", stamp the current baseline once, then migrate:
   ```bash
   cd backend && python3 -m alembic stamp 003_default_model_qwen3 && python3 -m alembic upgrade head
   ```

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

Builds Next.js static export, PyInstaller sidecar, and Tauri app:

```bash
npm run build
```

Copy `backend/.env` to `src-tauri/binaries/.env` before building so OAuth and database settings are picked up by the sidecar. Secrets are not embedded in the frontend bundle.

## Architecture

| Layer | Tech |
|-------|------|
| Shell | Tauri 2 (Rust) |
| UI | Next.js 14 static export |
| Backend | FastAPI sidecar on `127.0.0.1:8000` |
| LLM | Ollama (`qwen2.5:7b` default) |
| DB | SQLite (default) or PostgreSQL via `DATABASE_URL` |

## Product features

- First-run onboarding wizard for local Ollama
- Google OAuth setup wizard in Settings
- Named cross-product workflows
- Menu bar tray + global hotkey (`Cmd+Shift+G` / `Ctrl+Shift+G`)
- Read aloud on assistant messages (text-to-speech)
- Agent activity panel during chat
- Landing page at `landing/index.html` for GitHub Pages

## Scripts

| Command | Description |
|---------|-------------|
| `npm run dev` | Desktop app (auto-starts bundled backend) |
| `npm run db:migrate` | Apply Alembic migrations |
| `npm run build:sidecar` | Rebuild Python backend binary |
| `npm run build` | Full release build (.dmg / .app) |

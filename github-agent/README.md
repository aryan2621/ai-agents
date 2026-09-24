# GitHub Agent

A desktop AI assistant for GitHub (repos, issues, pull requests, code, and notifications). Built with Tauri, Next.js, FastAPI, local Ollama, and embedded SQLite.

**Tagline:** Your private, local AI for GitHub — repos, issues, pull requests, and notifications.

## Prerequisites

1. **Node.js 20+** and **Rust** (for Tauri)
2. **Python 3.11+**
3. **PostgreSQL** (optional) — embedded **SQLite** is used by default; no database setup required
4. **Ollama** — install from [ollama.com](https://ollama.com), then pull the default model: `ollama pull ministral-3:8b`
5. **GitHub OAuth App** — create an OAuth App at [GitHub Developer settings](https://github.com/settings/developers). Set the authorization callback URL to:
   ```
   http://127.0.0.1:8000/auth/github/callback
   ```

Do not run GitHub Agent and Google Agent at the same time — both bind port 8000.

## Setup

1. Copy environment file:
   ```bash
   cp backend/.env.example backend/.env
   ```
2. Edit `backend/.env` with your GitHub OAuth credentials:
   ```
   GITHUB_CLIENT_ID=your-oauth-app-client-id
   GITHUB_CLIENT_SECRET=your-oauth-app-client-secret
   DEFAULT_MODEL=ministral-3:8b
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

Global shortcut: `Cmd+Shift+H` (macOS) / `Ctrl+Shift+H` (Windows/Linux).

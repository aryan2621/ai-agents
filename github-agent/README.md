# GitHub Agent

A desktop AI assistant for GitHub (repos, issues, pull requests, code, and notifications). Built with Tauri, Next.js, FastAPI and a built-in llama.cpp model. Chats are saved as local JSON files.

**Tagline:** Your private, local AI for GitHub — repos, issues, pull requests, and notifications.

## Prerequisites

1. **Node.js 20+** and **Rust** (for Tauri)
2. **Python 3.11+**
3. **CMake** (to build the bundled llama.cpp server; `brew install cmake`)
4. **GitHub OAuth App** — create an OAuth App at [GitHub Developer settings](https://github.com/settings/developers). Set the authorization callback URL to:
   ```
   http://127.0.0.1:47831/auth/github/callback
   ```

### Ports

| | GitHub Agent | Google Agent |
|---|---|---|
| Backend (FastAPI) | 47831, fixed | 47832, fixed |
| Dev UI (`next dev`) | 47821, `GITHUB_AGENT_UI_PORT` | 47822, `GOOGLE_AGENT_UI_PORT` |
| llama-server | a free port picked at launch | same |

The two apps never share a port, so both can run at the same time. The backend port is fixed because
the OAuth redirect URI, the Tauri shell and the window's CSP all name it; it does not read `HOST` or
`PORT`. In dev, set `GITHUB_AGENT_UI_PORT` to move the UI; `npm run dev` stops with a message if the
port is taken.

## Setup

1. Copy environment file:
   ```bash
   cp backend/.env.example backend/.env
   ```
2. Edit `backend/.env` with your GitHub OAuth credentials:
   ```
   GITHUB_CLIENT_ID=your-oauth-app-client-id
   GITHUB_CLIENT_SECRET=your-oauth-app-client-secret
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
4. On first launch, download a model in the onboarding step (or Settings → Models). It runs on this Mac;
   nothing else to install. Chats, settings and models live in `~/Library/Application Support/GitHub Agent/`.

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

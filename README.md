# AI Agents

Two desktop AI assistants for macOS, whose AI runs on your Mac:

- **GitHub Agent**: repos, issues, pull requests, code and notifications
- **Google Agent**: Gmail, Calendar, Drive, Docs and Sheets

Each app has a chat window with a separate agent "room" per product, plus optional web search.
The AI model runs locally through llama.cpp; nothing you type goes to an AI company.

**[Download the latest release →](https://github.com/aryan2621/ai-agents/releases/latest)**

---

## Requirements

- A Mac with **Apple silicon** (M1 or newer), macOS 11 or later
- **8 GB of memory** or more (16 GB recommended for the larger models)
- About **3–17 GB of free disk space** for one AI model, depending on which one you pick
- A GitHub account (GitHub Agent) or a Google account (Google Agent)

## Install

1. Download `GitHub Agent_…_aarch64.dmg` and/or `Google Agent_…_aarch64.dmg` from the
   [Releases page](https://github.com/aryan2621/ai-agents/releases/latest).
2. Open the `.dmg` and drag the app into **Applications**.
3. Open the app. The first time, macOS blocks it (see below).

### "Apple could not verify…" / "can't be opened"

The apps are **not signed with an Apple Developer certificate**, so macOS warns about them the
first time. To open the app anyway:

1. Try to open the app once and click **Done** (or **OK**) on the warning.
2. Open **System Settings → Privacy & Security**, scroll down to the message about the app, and
   click **Open Anyway**. Confirm with your password or Touch ID.
3. Open the app again and click **Open**. macOS remembers this; you won't be asked again.

If macOS says the app **"is damaged and can't be opened"**, run this once in Terminal (use the
app's name), then open it normally:

```bash
xattr -dr com.apple.quarantine "/Applications/Google Agent.app"
```

This only removes the "downloaded from the internet" flag that macOS puts on the app.

## First run

The setup screens walk you through these, in order:

### 1. Download an AI model

Pick a model to download; it runs on your Mac and is stored in the app's data folder. The app
recommends one that fits your Mac:

| Model | Download | Good for |
|---|---|---|
| Qwen3.5 4B | 2.7 GB | Any Mac with 8 GB+; quick, simple requests |
| Qwen3.5 9B | 5.7 GB | 16 GB+; the best balance for multi-step tasks |
| Gemma 4 12B | 6.7 GB | 16 GB+; an alternative to Qwen |
| Gemma 4 26B A4B | 14.3 GB | 32 GB+; large but fast |
| Qwen3.8 27B | 16.5 GB | 32 GB+; most capable, slower |

You can download, switch or delete models later in **Settings → Models**. Only the selected model
is loaded, and it stops when you quit the app. If you run both apps at once, each loads its own
model, so pick small ones if your Mac has 16 GB or less.

### 2. Connect your own sign-in client (one time)

The apps don't come with a shared GitHub or Google sign-in key. Instead you create your own, for
free, and paste it into the app. This way no secret is shipped inside the app, and your
sign-in goes straight from your Mac to GitHub or Google.

The app shows this form before the sign-in button (and later in **Settings → GitHub OAuth /
Google OAuth**).

<details>
<summary><b>GitHub Agent: create a GitHub OAuth App (2 minutes)</b></summary>

1. Go to [github.com/settings/developers](https://github.com/settings/developers) → **OAuth Apps**
   → **New OAuth App**.
2. Fill in:
   - **Application name**: anything, e.g. `My GitHub Agent`
   - **Homepage URL**: `http://127.0.0.1:47831`
   - **Authorization callback URL**: `http://127.0.0.1:47831/auth/github/callback`
3. Click **Register application**.
4. Copy the **Client ID**. Click **Generate a new client secret** and copy it.
5. Paste both into GitHub Agent and click **Save**.
</details>

<details>
<summary><b>Google Agent: create a Google Cloud OAuth client (about 10 minutes)</b></summary>

1. Go to [console.cloud.google.com](https://console.cloud.google.com/) and create a project
   (any name).
2. **Enable the APIs**: open **APIs & Services → Library** and enable **Gmail API**,
   **Google Calendar API**, **Google Drive API**, **Google Docs API** and **Google Sheets API**.
3. **Set up the consent screen**: open **Google Auth Platform** (or **APIs & Services → OAuth
   consent screen**) → **Get started**. Enter an app name and your email, choose
   **External** as the audience, and finish.
4. **Add yourself as a test user**: under **Audience → Test users**, add the Google account you'll
   sign in with.
5. **Create the client**: under **Clients** (or **Credentials → Create credentials → OAuth client
   ID**), choose application type **Desktop app**, give it a name, and click **Create**.
6. Copy the **Client ID** and **Client secret**, paste both into Google Agent, and click **Save**.

When you sign in, Google shows **"Google hasn't verified this app"**. That's expected: it's
your own app. Click **Continue** (or **Advanced → Go to … (unsafe)**). While your Google app is in
testing mode, Google asks you to sign in again about once a week.
</details>

### 3. Sign in

Click **Continue with GitHub** or **Continue with Google**. Your browser opens; approve access,
then return to the app. You can grant or re-grant permissions per agent later.

---

## Privacy

**What stays on your Mac**

- **The AI.** Messages are answered by the model running on your Mac. No AI company sees your
  chats, emails, files or code.
- **Your chats, settings and sign-in.** They're stored only in the app's data folder:
  - `~/Library/Application Support/GitHub Agent/`
  - `~/Library/Application Support/Google Agent/`
- **Read aloud** uses macOS's built-in voice.

**What leaves your Mac, and only when you use it**

| Goes to | When | What |
|---|---|---|
| GitHub (api.github.com) | You ask GitHub Agent about your repos, issues, PRs… | The requests needed to answer, using your sign-in |
| Google APIs | You ask Google Agent about Gmail, Calendar, Drive, Docs, Sheets | The requests needed to answer, using your sign-in |
| Hugging Face | You download a model | A normal file download (no account) |
| Tavily | You use the **Web** agent with your own Tavily key | Your search query |
| Google speech recognition | You use **voice input** (the microphone button) | The recorded audio, to turn it into text |

There is no analytics, tracking or telemetry, and no server run by this project.

**Permissions the apps ask for**

- **GitHub Agent**: your profile and email, repositories (`repo`) and notifications.
- **Google Agent**: your profile and email, Gmail (read, send, organize; not permanent delete),
  Calendar, Drive, Docs and Sheets.

Actions that change things (sending an email, creating an event, merging a pull request…) only
happen when you ask for them in a message.

**Good to know**

- Your sign-in tokens are kept in the app's data folder, which only your macOS user account can
  read. They are not encrypted on disk.
- To disconnect an app, sign out in the app, and revoke access at
  [github.com/settings/applications](https://github.com/settings/applications) or
  [myaccount.google.com/permissions](https://myaccount.google.com/permissions).

## Uninstall

1. Quit the app and drag it from **Applications** to the Trash.
2. Delete its data folder (chats, settings, sign-in and downloaded models):

   ```bash
   rm -rf ~/Library/Application\ Support/GitHub\ Agent   # GitHub Agent
   rm -rf ~/Library/Application\ Support/Google\ Agent   # Google Agent
   ```

3. Optionally, revoke its access (links above) and delete the OAuth App / Google Cloud client you
   created.

---

## For developers

Each app is a Tauri desktop shell with a Next.js UI, a Python (FastAPI) backend and a bundled
llama.cpp server. See [`github-agent/README.md`](github-agent/README.md) and
[`google-agent/README.md`](google-agent/README.md) for building and running from source.
Pushing a `v*` tag builds both apps and publishes them on the Releases page.

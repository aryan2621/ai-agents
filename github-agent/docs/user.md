# GitHub Agent: user guide

[← Back to README](../README.md) · [Developer guide](dev.md)

- [Install](#install) · [First run](#first-run) · [Rooms](#rooms) · [Settings](#settings) · [Privacy](#privacy) · [Troubleshooting](#troubleshooting)

## Install

1. Download [`GitHub.Agent_0.1.0_aarch64.dmg`](https://github.com/aryan2621/ai-agents/releases/latest/download/GitHub.Agent_0.1.0_aarch64.dmg)
   (Mac with Apple silicon, 8 GB of memory or more).
2. Open it, drag **GitHub Agent** into **Applications**, and open it.

**"Apple could not verify GitHub Agent is free of malware":** the app isn't signed with a paid
Apple Developer certificate, so macOS warns you the first time. Click **Done**, open **System
Settings → Privacy & Security**, scroll down, click **Open Anyway** and confirm. If macOS says
the app **"is damaged and can't be opened"**, run this once in Terminal and open it again:

```bash
xattr -dr com.apple.quarantine "/Applications/GitHub Agent.app"
```

## First run

**1. Download an AI model.** It runs on your Mac. The app recommends the strongest one your Mac's
memory runs well; you can change it later in **Settings → Models**.

| Model | Download | Memory | |
|---|---|---|---|
| Qwen3.5 4B | 2.7 GB | 8 GB | Small and quick; simple requests |
| Qwen3.5 9B | 5.7 GB | 16 GB | The best balance for multi-step requests |
| Gemma 4 12B | 6.7 GB | 16 GB | Google's model; a good second opinion |
| Gemma 4 26B A4B | 14.3 GB | 32 GB | Large but fast |
| Qwen3.8 27B | 16.5 GB | 32 GB | The most capable; slower |

A model you already downloaded in Google Agent or Relay is reused.

**2. Connect your own GitHub OAuth app** (free, about 2 minutes). No shared key ships with the
app, so you use your own:

1. Open [github.com/settings/developers](https://github.com/settings/developers) → **OAuth Apps** → **New OAuth App**.
2. Application name: *GitHub Agent*. Homepage URL: `http://127.0.0.1:47831`.
3. Authorization callback URL: `http://127.0.0.1:47831/auth/github/callback`
4. **Register application**, then **Generate a new client secret**. Copy the **Client ID** and
   the **Client Secret** (GitHub shows the secret only once).
5. Paste both into the app and save.

**3. Sign in with GitHub** and approve the access. The app asks for your profile and email,
repositories (`repo`) and notifications.

## Rooms

Each room is an agent for one job. Every room can also search the web.

| Room | Ask things like |
|---|---|
| **Repos** | "My Kotlin repos", "Show the README of my-app", "Latest release of my-app" |
| **Issues** | "Issues assigned to me", "Summarise issue 42 in my-app", "Comment on #42: fixed in 1.2", "Open an issue: login button is broken" |
| **Pull requests** | "My open PRs", "What files does PR 17 change?", "Merge PR 17" |
| **Code** | "Show src/main.ts in my-app", "Where is `parseConfig` used?", "Last 5 commits on main" |
| **Notifications** | "What's unread?", "Mark that one as read" |
| **Web Search** | Research on the public web (needs a Tavily key) |

Turn rooms on or off in **Settings → Agents**. **⌘⇧H** brings the app to the front from any app.

## Settings

- **General:** theme, text size, chat behaviour.
- **Models:** download, choose or delete AI models.
- **Agents:** which rooms appear.
- **Web search:** your [Tavily](https://tavily.com) API key (free tier available), for web research.
- **GitHub OAuth:** your Client ID and Client Secret.
- **Profile:** the signed-in account; sign out.

## Privacy

- The AI runs on your Mac. Chats, settings, models and sign-in are in
  `~/Library/Application Support/GitHub Agent/`.
- The app contacts GitHub only to do what you ask, and Hugging Face to download models.
- **Voice input** (optional) sends the recording to Google to turn it into text. **Web search**
  (optional) sends your search to Tavily.
- No analytics or tracking.

## Troubleshooting

| Problem | Fix |
|---|---|
| GitHub says **"The redirect_uri is not associated with this application"** | The callback URL must be exactly `http://127.0.0.1:47831/auth/github/callback` (not `localhost`). |
| "Bad credentials" or sign-in fails after saving | The Client Secret is wrong or was regenerated. Generate a new one and save both again. |
| "No AI model is downloaded yet" | **Settings → Models**, download one. |
| Answers are slow | Pick a smaller model in **Settings → Models**, or close other large apps. |
| A private repo isn't found | Sign out and in again, and approve repository access. For organisation repos, the organisation may need to approve your OAuth app. |

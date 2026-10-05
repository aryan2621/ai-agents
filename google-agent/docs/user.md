# Google Agent: user guide

[← Back to README](../README.md) · [Google setup](google-setup.md) · [Developer guide](dev.md)

- [Install](#install) · [First run](#first-run) · [Rooms](#rooms) · [Settings](#settings) · [Privacy](#privacy) · [Troubleshooting](#troubleshooting)

## Install

1. Download [`Google.Agent_0.1.0_aarch64.dmg`](https://github.com/aryan2621/ai-agents/releases/latest/download/Google.Agent_0.1.0_aarch64.dmg)
   (Mac with Apple silicon, 8 GB of memory or more).
2. Open it, drag **Google Agent** into **Applications**, and open it.

**"Apple could not verify Google Agent is free of malware":** the app isn't signed with a paid
Apple Developer certificate, so macOS warns you the first time. Click **Done**, open **System
Settings → Privacy & Security**, scroll down, click **Open Anyway** and confirm. If macOS says
the app **"is damaged and can't be opened"**, run this once in Terminal and open it again:

```bash
xattr -dr com.apple.quarantine "/Applications/Google Agent.app"
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

A model you already downloaded in GitHub Agent or Relay is reused.

**2. Connect your own Google Cloud app** (free, about 5 minutes, once): follow the
**[Google setup guide](google-setup.md)**, then paste the Client ID and Client Secret into the app.

**3. Sign in with Google.** Google says "Google hasn't verified this app": that's expected,
because it's your own app. Click **Advanced → Go to Google Agent (unsafe)**, and **tick every
box** so each room can work.

## Rooms

Each room is an agent for one job. Every room can also search the web.

| Room | Ask things like |
|---|---|
| **Gmail** | "What's unread?", "Find the invoice from Acme", "Reply: thanks, see you Monday", "Draft an email to Sam about the launch", "Archive that" |
| **Calendar** | "What's on tomorrow?", "Am I free Thursday 2–4?", "Add lunch with Priya on Friday at 1", "Move it to 2" |
| **Drive** | "My recent files", "Find the Q3 deck", "What's shared with me?", "Make a folder called Taxes" |
| **Docs** | "Read my meeting notes doc", "Add these action items to it", "Create a doc with this outline" |
| **Sheets** | "Summarise the budget sheet", "Add a row: Uber, 450", "Make a sheet of these expenses" |
| **Web Search** | Research on the public web (needs a Tavily key) |

Turn rooms on or off in **Settings → Agents**. **⌘⇧G** brings the app to the front from any app.

## Settings

- **General:** theme, text size, chat behaviour.
- **Models:** download, choose or delete AI models.
- **Agents:** which rooms appear.
- **Web search:** your [Tavily](https://tavily.com) API key (free tier available), for web research.
- **Google OAuth:** your Client ID and Client Secret, with the setup steps.
- **Profile:** the signed-in account and its permissions; sign out.

## Privacy

- The AI runs on your Mac. Chats, settings, models, your Client ID and Secret, and sign-in are in
  `~/Library/Application Support/Google Agent/`.
- The app contacts Google only to do what you ask, and Hugging Face to download models.
- **Voice input** (optional) sends the recording to Google to turn it into text. **Web search**
  (optional) sends your search to Tavily.
- No analytics or tracking.

## Troubleshooting

Google sign-in problems (access blocked, signed out every week, wrong client…): see
[Google setup → Troubleshooting](google-setup.md#troubleshooting).

| Problem | Fix |
|---|---|
| "No AI model is downloaded yet" | **Settings → Models**, download one. |
| A room says it can't reach Gmail, Calendar… | You unticked its box at sign-in. Sign out, sign in again, and tick every box. |
| Answers are slow | Pick a smaller model in **Settings → Models**, or close other large apps. |

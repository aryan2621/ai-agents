# AI Agents

Two macOS assistants whose AI runs on your Mac: **GitHub Agent** (repos, issues, pull requests,
notifications) and **Google Agent** (Gmail, Calendar, Drive, Docs, Sheets).

**[Download the latest release →](https://github.com/aryan2621/ai-agents/releases/latest)**
Requires a Mac with Apple silicon (M1 or newer) and 8 GB of memory or more.

## Opening the app

The apps aren't signed with an Apple Developer certificate, so macOS blocks them the first time:

1. Open the app once and dismiss the warning.
2. Go to **System Settings → Privacy & Security** and click **Open Anyway**.

If macOS says the app "is damaged", run this once in Terminal, then open it again:

```bash
xattr -dr com.apple.quarantine "/Applications/Google Agent.app"
```

## First run

1. **Download a model.** The app recommends one that fits your Mac.
2. **Connect your own sign-in client.** No shared key ships with the app, so create one (free)
   and paste its Client ID and Client Secret into the app:
   - **GitHub:** [github.com/settings/developers](https://github.com/settings/developers) → New
     OAuth App. Homepage URL `http://127.0.0.1:47831`, callback URL
     `http://127.0.0.1:47831/auth/github/callback`.
   - **Google:** in [Google Cloud Console](https://console.cloud.google.com/), create a project,
     enable the Gmail, Calendar, Drive, Docs and Sheets APIs, set up the consent screen and add
     yourself as a test user, then create an OAuth client of type **Desktop app**. When signing
     in, continue past "Google hasn't verified this app": it's your own app.
3. **Sign in** with GitHub or Google.

## Privacy

- The AI runs on your Mac. Chats, settings and sign-in stay in
  `~/Library/Application Support/<App name>/`.
- The app contacts GitHub or Google only to do what you ask, and Hugging Face to download models.
- **Voice input** sends the recorded audio to Google to turn it into text, and the **Web** agent
  sends your search to Tavily. Both are optional.
- No analytics or tracking.

## Building from source

See [`github-agent/README.md`](github-agent/README.md) and
[`google-agent/README.md`](google-agent/README.md).

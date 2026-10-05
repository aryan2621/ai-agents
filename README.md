# AI Agents

**Two Mac assistants whose AI runs on your Mac. Ask in plain words; they do the work in GitHub or Google.**

| | | |
|---|---|---|
| **[GitHub Agent](github-agent/)** | Repos, issues, pull requests, code and notifications | [⬇ Download](https://github.com/aryan2621/ai-agents/releases/latest/download/GitHub.Agent_0.1.0_aarch64.dmg) |
| **[Google Agent](google-agent/)** | Gmail, Calendar, Drive, Docs and Sheets | [⬇ Download](https://github.com/aryan2621/ai-agents/releases/latest/download/Google.Agent_0.1.0_aarch64.dmg) |

Mac with Apple silicon (M1 or newer), 8 GB of memory or more ·
[all downloads](https://github.com/aryan2621/ai-agents/releases/latest)

- **Private:** the AI runs on your Mac. Chats and settings stay there.
- **Your own keys:** no shared sign-in ships with the apps. Each person connects their own free
  GitHub or Google app (a few minutes, once; each app's guide has the steps).
- **Rooms:** one room per job (Gmail, Calendar…, or Issues, Pull requests…), each with web search.

## Install

1. Open the `.dmg` and drag the app into **Applications**, then open it.
2. If macOS says **"Apple could not verify … is free of malware"**: click **Done**, go to
   **System Settings → Privacy & Security**, scroll down and click **Open Anyway**. (The apps
   aren't signed with a paid Apple certificate; that's the only reason for the warning.)
3. If it says the app **"is damaged"**, run this once in Terminal and open it again:
   ```bash
   xattr -dr com.apple.quarantine "/Applications/GitHub Agent.app"
   xattr -dr com.apple.quarantine "/Applications/Google Agent.app"
   ```
4. The first run sets you up: download an AI model (it recommends one for your Mac), connect your
   sign-in app, and sign in. Details: [GitHub Agent](github-agent/docs/user.md#first-run) ·
   [Google Agent](google-agent/docs/user.md#first-run).

## Privacy

- The AI runs on your Mac. Chats, settings and sign-in stay in `~/Library/Application Support/<App name>/`.
- The apps contact GitHub or Google only to do what you ask, and Hugging Face to download models.
- Optional: **voice input** sends the recorded audio to Google to turn it into text, and **web
  search** sends your search to Tavily.
- No analytics or tracking.

## Build from source

Each app has a developer guide: [GitHub Agent](github-agent/docs/dev.md) · [Google Agent](google-agent/docs/dev.md).

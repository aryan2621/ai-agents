# GitHub Agent

**Your private AI for GitHub. Ask about repos, issues, pull requests and notifications, in plain words.**

<!-- DEMO VIDEO: paste the https://github.com/user-attachments/assets/... link on the next line -->

- *"Which of my PRs are still open?"*, *"Summarise issue 42 in my-app"*, *"What's new in my notifications?"*
- Opens issues, comments, creates and merges pull requests, reads code and commits, when you ask.
- The AI runs on your Mac. You sign in with your own GitHub OAuth app; nothing shared ships with it.

**[⬇ Download for macOS](https://github.com/aryan2621/ai-agents/releases/latest/download/GitHub.Agent_0.1.0_aarch64.dmg)**
· Apple silicon, 8 GB of memory or more

📖 **[User guide](docs/user.md)** — first run, what each room does, settings, troubleshooting
🛠 **[Developer guide](docs/dev.md)** — build from source, ports, architecture

## Install

1. Open the `.dmg`, drag **GitHub Agent** into **Applications**, and open it.
2. If macOS says **"Apple could not verify GitHub Agent is free of malware"**: click **Done**, go to
   **System Settings → Privacy & Security**, and click **Open Anyway**.
3. If it says the app **"is damaged"**, run this once in Terminal and open it again:
   ```bash
   xattr -dr com.apple.quarantine "/Applications/GitHub Agent.app"
   ```

## Quick start

1. **Download a model** when asked (it recommends one for your Mac).
2. **Connect GitHub:** [github.com/settings/developers](https://github.com/settings/developers) →
   **New OAuth App**, homepage `http://127.0.0.1:47831`, callback
   `http://127.0.0.1:47831/auth/github/callback`. Paste its Client ID and Client Secret.
3. **Sign in with GitHub**, pick a room, and ask. **⌘⇧H** shows the app from anywhere.

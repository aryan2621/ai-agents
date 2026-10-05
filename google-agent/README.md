# Google Agent

**Your private AI for Google Workspace. Ask about your Gmail, Calendar, Drive, Docs and Sheets, in plain words.**

<!-- DEMO VIDEO: paste the https://github.com/user-attachments/assets/... link on the next line -->

- *"What's unread from this week?"*, *"Am I free Thursday afternoon?"*, *"Make a sheet of these expenses"*
- Sends and drafts email, creates calendar events, edits Docs and Sheets, finds Drive files, when you ask.
- The AI runs on your Mac. You sign in with your own Google Cloud app; nothing shared ships with it.

**[⬇ Download for macOS](https://github.com/aryan2621/ai-agents/releases/latest/download/Google.Agent_0.1.0_aarch64.dmg)**
· Apple silicon, 8 GB of memory or more

📖 **[User guide](docs/user.md)** — first run, what each room does, settings, troubleshooting
☁️ **[Google setup](docs/google-setup.md)** — connect your own Google account, step by step
🛠 **[Developer guide](docs/dev.md)** — build from source, ports, architecture

## Install

1. Open the `.dmg`, drag **Google Agent** into **Applications**, and open it.
2. If macOS says **"Apple could not verify Google Agent is free of malware"**: click **Done**, go to
   **System Settings → Privacy & Security**, and click **Open Anyway**.
3. If it says the app **"is damaged"**, run this once in Terminal and open it again:
   ```bash
   xattr -dr com.apple.quarantine "/Applications/Google Agent.app"
   ```

## Quick start

1. **Download a model** when asked (it recommends one for your Mac).
2. **Connect Google:** make your own client in Google Cloud (5 minutes, once:
   [Google setup guide](docs/google-setup.md)) and paste its Client ID and Client Secret.
3. **Sign in with Google**, tick every box, pick a room, and ask. **⌘⇧G** shows the app from anywhere.

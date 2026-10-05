# Set up Google sign-in for Google Agent

[← README](../README.md) · [User guide](user.md)

Google Agent signs in with **your own** free Google Cloud project. No Google keys ship with the
app, so every person uses their own account and their own keys, and nobody else's. It takes
about 5 minutes, once.

When you're done, paste the Client ID and Client Secret into the app (first run, the sign-in
screen, or **Settings → Google OAuth**).

## The steps

Use the Google account you want Google Agent to work with. At the top of every Cloud Console
page, check the project picker shows the project you created.

**1. Create a project.** Open [Create a project](https://console.cloud.google.com/projectcreate),
name it anything (for example *Google Agent*) and click **Create**.

**2. Turn on the APIs.** Open [Enable the APIs](https://console.cloud.google.com/flows/enableapi?apiid=gmail.googleapis.com,calendar-json.googleapis.com,drive.googleapis.com,docs.googleapis.com,sheets.googleapis.com),
check your project is selected, click **Next**, then **Enable**. That turns on Gmail, Google
Calendar, Google Drive, Google Docs and Google Sheets in one go.

**3. Set up the sign-in screen.** Open [Google Auth Platform](https://console.cloud.google.com/auth/overview)
and click **Get started**:
- App name: *Google Agent*. User support email: your email.
- Audience: **External**.
- Contact information: your email.
- Agree to the policy and click **Create**.

**4. Publish it, so you stay signed in.** Open [Audience](https://console.cloud.google.com/auth/audience),
click **Publish app** and confirm.

While a project is in *Testing*, Google signs you out every 7 days. Publishing stops that. It
doesn't need Google's review for your own use; it only means the "unverified app" screen
appears when you sign in (step 7). If you'd rather keep it in Testing, add your email under
**Test users** on the same page, and sign in again each week.

**5. Create the client.** Open [Clients](https://console.cloud.google.com/auth/clients) and click
**Create client**:
- Application type: **Desktop app** (no redirect URI needed: Desktop clients accept the app's
  local `127.0.0.1` address automatically)
- Name: *Google Agent*
- Click **Create**.

Copy the **Client ID** and the **Client Secret** now. Google shows the secret only once (if you
lose it, open the client and add a new secret).

**6. Paste them into Google Agent** and click **Save OAuth credentials**.

**7. Sign in with Google.** Your browser opens Google's sign-in:
1. Pick your account.
2. Google says **"Google hasn't verified this app"**. That's expected: it's your own app. Click
   **Advanced**, then **Go to Google Agent (unsafe)**.
3. Tick **every** box (Gmail, Calendar, Drive, Docs, Sheets) and click **Continue**. An agent
   whose box is unticked can't work until you sign in again and tick it.

## Your privacy

- **Your keys stay on your Mac.** The Client ID and Client Secret are saved in
  `~/Library/Application Support/Google Agent/`, in a file only your user can read. They're never
  in the app or a download.
- **Each user brings their own.** Someone else using Google Agent sets up their own project; they
  can't use yours, and you can't use theirs.
- **The app never sees your password.** You sign in on Google's own page in your browser.
- **No server in between.** Requests go straight from your Mac to Google, and the AI runs on
  your Mac.

To withdraw access, sign out in the app, or remove *Google Agent* at
[myaccount.google.com/connections](https://myaccount.google.com/connections).

## Good to know

- **Up to 100 people** can ever sign in to an unverified project. Plenty for you; each person
  should use their own project anyway.
- Google Agent asks for broad permissions (read and send email, edit calendar, Drive, Docs and
  Sheets) because its agents act on them for you. That's also why Google shows the unverified
  screen: the permissions are yours, granted to your own app.

## Troubleshooting

| You see | Fix |
|---|---|
| "That isn't a Client ID" | Copy the Client ID, not the project ID or number. It ends in `.apps.googleusercontent.com`. |
| "Google didn't accept your Client ID and Client Secret" | They're from different clients, or the secret was reset. Copy both from the same Desktop app client (add a new secret if needed) and save again. |
| "Google signed you out" every week | Step 4: publish the project. |
| Google shows **"Access blocked"** or **"Error 403: access_denied"** | The project is in Testing and your account isn't a test user. Do step 4 (publish), or add your email under Test users. |
| Google shows **"Error 400: redirect_uri_mismatch"** | The client isn't a **Desktop app**. Create a new client of type Desktop app (step 5). |
| An agent says an API "has not been used in project … or it is disabled" | Step 2, in the same project as the client. Wait a minute after enabling. |
| An agent can't reach Gmail, Calendar, … after signing in | You unticked its box. Sign out, sign in again, and tick every box. |

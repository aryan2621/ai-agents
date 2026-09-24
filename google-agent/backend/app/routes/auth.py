import logging
import secrets
from urllib.parse import quote

from fastapi import APIRouter, Depends, Header, HTTPException
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.platform.app_config import oauth_is_configured, resolve_google_credentials
from app.db.database import get_db
from app.models.auth import GoogleUserResponse
from app.services.auth.auth_service import delete_user_session, get_user_by_access_token, to_user_response
from app.services.auth.token_crypto import decrypt_token
from app.services.auth.google_oauth import (
    GOOGLE_OAUTH_REDIRECT_URI,
    build_google_auth_url,
    exchange_code,
    fetch_profile_picture,
)
from app.services.auth import oauth_pending

router = APIRouter(prefix="/auth", tags=["auth"])
logger = logging.getLogger(__name__)


def _extract_bearer(authorization: str | None) -> str:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")
    return authorization[7:]


def _callback_html(title: str, message: str, deep_link: str | None = None) -> str:
    deep_link_script = ""
    if deep_link:
        deep_link_script = f"""
        <script>
          (function() {{
            function notifyApp() {{
              var iframe = document.createElement("iframe");
              iframe.style.display = "none";
              iframe.src = {deep_link!r};
              document.body.appendChild(iframe);
              setTimeout(function() {{
                if (iframe.parentNode) iframe.parentNode.removeChild(iframe);
              }}, 2000);
            }}
            function tryClose() {{
              window.close();
            }}
            notifyApp();
            setTimeout(tryClose, 300);
            setTimeout(tryClose, 1000);
            setTimeout(function() {{
              var hint = document.getElementById("close-hint");
              if (hint) hint.style.display = "block";
            }}, 1200);
          }})();
        </script>
        """
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{title}</title>
  <style>
    body {{
      font-family: ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      background: #ffffff;
      color: #0a0a0a;
      display: flex;
      align-items: center;
      justify-content: center;
      min-height: 100vh;
      margin: 0;
    }}
    .card {{
      max-width: 420px;
      padding: 32px;
      border: 1px solid #e5e5e5;
      border-radius: 16px;
      background: #fafafa;
      text-align: center;
    }}
    h1 {{
      font-family: "SF Pro Rounded", ui-rounded, -apple-system, system-ui, sans-serif;
      font-size: 20px;
      font-weight: 500;
      margin: 0 0 12px;
    }}
    p {{ color: #737373; line-height: 1.5; margin: 0; font-size: 14px; }}
    #close-hint {{ display: none; margin-top: 16px; color: #525252; }}
    button {{
      margin-top: 16px;
      padding: 8px 16px;
      border: 1px solid #e5e5e5;
      border-radius: 8px;
      background: #fff;
      color: #0a0a0a;
      font-size: 14px;
      cursor: pointer;
    }}
    button:hover {{ background: #f5f5f5; }}
  </style>
  {deep_link_script}
</head>
<body>
  <div class="card">
    <h1>{title}</h1>
    <p>{message}</p>
    <p id="close-hint">You can close this window now.</p>
    <button type="button" onclick="window.close()">Close window</button>
  </div>
</body>
</html>"""


def _popup_launcher_html(auth_url: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Google sign-in</title>
  <style>
    body {{
      font-family: ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      background: #fafafa;
      color: #0a0a0a;
      display: flex;
      align-items: center;
      justify-content: center;
      min-height: 100vh;
      margin: 0;
    }}
    .card {{
      max-width: 420px;
      padding: 32px;
      border: 1px solid #e5e5e5;
      border-radius: 16px;
      background: #ffffff;
      text-align: center;
    }}
    h1 {{
      font-family: "SF Pro Rounded", ui-rounded, -apple-system, system-ui, sans-serif;
      font-size: 20px;
      font-weight: 500;
      margin: 0 0 12px;
    }}
    p {{ color: #737373; line-height: 1.5; margin: 0 0 20px; font-size: 14px; }}
    button {{
      width: 100%;
      padding: 11px 16px;
      border: 1px solid #e5e5e5;
      border-radius: 8px;
      background: #0a0a0a;
      color: #ffffff;
      font-size: 14px;
      font-weight: 500;
      cursor: pointer;
    }}
    button:hover {{ background: #262626; }}
  </style>
</head>
<body>
  <div class="card">
    <h1>Google sign-in</h1>
    <p>Click below to open Google sign-in. This tab will close when you finish.</p>
    <button type="button" id="signin-btn">Continue with Google</button>
  </div>
  <script>
    (function() {{
      var authUrl = {auth_url!r};
      var popup = null;
      var timer = null;

      function watchPopup() {{
        if (timer) clearInterval(timer);
        timer = setInterval(function() {{
          if (popup && popup.closed) {{
            clearInterval(timer);
            window.close();
          }}
        }}, 500);
      }}

      document.getElementById("signin-btn").addEventListener("click", function() {{
        popup = window.open(
          authUrl,
          "google_oauth",
          "width=520,height=720,menubar=no,toolbar=no,location=yes,status=no,resizable=yes,scrollbars=yes"
        );
        if (!popup) {{
          window.location.href = authUrl;
          return;
        }}
        popup.focus();
        watchPopup();
      }});
    }})();
  </script>
</body>
</html>"""


@router.get("/google/url")
async def google_auth_url():
    client_id, _ = resolve_google_credentials()
    if not client_id:
        raise HTTPException(
            status_code=500,
            detail="Google OAuth is not configured. Add credentials in Settings → Google OAuth.",
        )
    state = secrets.token_urlsafe(24)
    oauth_pending.mark_pending(state)
    return {
        "url": build_google_auth_url(client_id, state),
        "state": state,
    }


@router.get("/google/status/{state}", response_model=GoogleUserResponse)
async def google_auth_status(state: str):
    entry = oauth_pending.get(state)
    if entry is None:
        raise HTTPException(status_code=404, detail="Unknown or expired OAuth session")
    if entry.status == "pending":
        raise HTTPException(status_code=404, detail="Authentication still in progress")
    if entry.status == "error":
        raise HTTPException(status_code=400, detail=entry.error or "Authentication failed")
    return entry.user


@router.get("/google/begin")
async def google_auth_begin(state: str):
    """Opens Google OAuth in a popup so the callback window can close itself."""
    if not state or oauth_pending.get(state) is None:
        raise HTTPException(status_code=400, detail="Invalid or expired OAuth state")

    client_id, _ = resolve_google_credentials()
    if not client_id:
        raise HTTPException(
            status_code=500,
            detail="Google OAuth is not configured. Add credentials in Settings → Google OAuth.",
        )

    auth_url = build_google_auth_url(client_id, state)
    return HTMLResponse(_popup_launcher_html(auth_url))


@router.get("/google/callback")
async def google_browser_callback(
    code: str | None = None,
    error: str | None = None,
    state: str | None = None,
    session: AsyncSession = Depends(get_db),
):
    """Browser redirect target; completes auth and shows a success page."""
    if not state or oauth_pending.get(state) is None:
        raise HTTPException(status_code=400, detail="Invalid or expired OAuth state")

    if error:
        oauth_pending.fail(state, error)
        return HTMLResponse(
            _callback_html(
                "Sign-in failed",
                "Return to Google Agent and try again.",
            ),
            status_code=400,
        )

    if not code:
        raise HTTPException(status_code=400, detail="Missing authorization code")

    try:
        user = await exchange_code(session, code, GOOGLE_OAUTH_REDIRECT_URI)
        oauth_pending.complete(state, user)
    except ValueError as exc:
        oauth_pending.fail(state, str(exc))
        return HTMLResponse(
            _callback_html("Sign-in failed", str(exc)),
            status_code=400,
        )
    except Exception as exc:
        logger.exception("OAuth callback failed for state=%s", state)
        oauth_pending.fail(state, "Internal error during sign-in")
        return HTMLResponse(
            _callback_html(
                "Sign-in failed",
                f"Something went wrong completing sign-in: {exc}",
            ),
            status_code=500,
        )

    deep_link = f"google-agent://oauth/callback?state={quote(state)}"
    return HTMLResponse(
        _callback_html(
            "Signed in successfully",
            "Returning to Google Agent…",
            deep_link=deep_link,
        )
    )


@router.get("/me", response_model=GoogleUserResponse)
async def get_me(
    authorization: str | None = Header(default=None),
    session: AsyncSession = Depends(get_db),
):
    access_token = _extract_bearer(authorization)
    row = await get_user_by_access_token(session, access_token)
    if row is None:
        raise HTTPException(status_code=401, detail="Invalid session")
    user, token = row
    if not (user.picture or "").strip() and token.google_access_token:
        picture = await fetch_profile_picture(decrypt_token(token.google_access_token))
        if picture:
            user.picture = picture
            await session.commit()
            await session.refresh(user)
    from app.services.auth.auth_service import StoredCredentials

    return to_user_response(
        StoredCredentials(
            user_id=user.id,
            email=user.email,
            name=user.name,
            picture=user.picture,
            session_token=token.access_token,
            google_access_token=token.google_access_token,
            refresh_token=token.refresh_token,
            expires_at=token.expires_at,
            granted_scopes=token.granted_scopes or "",
        )
    )


@router.post("/logout")
async def logout(
    authorization: str | None = Header(default=None),
    session: AsyncSession = Depends(get_db),
):
    access_token = _extract_bearer(authorization)
    await delete_user_session(session, access_token)
    return {"status": "ok"}

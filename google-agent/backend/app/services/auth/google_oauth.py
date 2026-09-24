import time

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.services.platform.app_config import resolve_google_credentials
from app.models.auth import GoogleUserResponse
from app.services.auth.auth_service import (
    StoredCredentials,
    get_credentials_by_access_token,
    is_expired,
    new_session_token,
    to_user_response,
    update_google_access_token,
    upsert_user_with_token,
)
from app.services.auth.scope_registry import scopes_to_string

GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v2/userinfo"
GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"

# Desktop OAuth clients must use loopback; Google auto-allows http://127.0.0.1 for Desktop type.
GOOGLE_OAUTH_REDIRECT_URI = "http://127.0.0.1:8000/auth/google/callback"

OAUTH_SCOPES = (
    "openid",
    "email",
    "profile",
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/calendar",
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/documents",
    "https://www.googleapis.com/auth/spreadsheets",
)


def build_google_auth_url(client_id: str, state: str) -> str:
    from urllib.parse import urlencode

    params = {
        "client_id": client_id,
        "redirect_uri": GOOGLE_OAUTH_REDIRECT_URI,
        "response_type": "code",
        "scope": " ".join(OAUTH_SCOPES),
        "access_type": "offline",
        "prompt": "consent",
        "state": state,
    }
    return f"{GOOGLE_AUTH_URL}?{urlencode(params)}"


async def exchange_code(
    session: AsyncSession, code: str, redirect_uri: str
) -> GoogleUserResponse:
    client_id, client_secret = resolve_google_credentials()
    if not client_id or not client_secret:
        raise ValueError(
            "Google OAuth is not configured. Add credentials in Settings → Google OAuth."
        )

    async with httpx.AsyncClient(timeout=30.0) as client:
        token_resp = await client.post(
            GOOGLE_TOKEN_URL,
            data={
                "code": code,
                "client_id": client_id,
                "client_secret": client_secret,
                "redirect_uri": redirect_uri,
                "grant_type": "authorization_code",
            },
        )
        if token_resp.status_code != 200:
            raise ValueError(f"Token exchange failed: {token_resp.text}")

        token_data = token_resp.json()
        access_token = token_data["access_token"]
        refresh_token = token_data.get("refresh_token", "")
        expires_in = int(token_data.get("expires_in", 3600))
        expires_at = int(time.time()) + expires_in
        granted_scopes = scopes_to_string(
            token_data.get("scope", "").split() if token_data.get("scope") else list(OAUTH_SCOPES)
        )

        user_resp = await client.get(
            GOOGLE_USERINFO_URL,
            headers={"Authorization": f"Bearer {access_token}"},
        )
        if user_resp.status_code != 200:
            raise ValueError(f"Userinfo fetch failed: {user_resp.text}")

        user_data = user_resp.json()

    session_token = new_session_token()
    creds = StoredCredentials(
        user_id=user_data["id"],
        email=user_data.get("email", ""),
        name=user_data.get("name", user_data.get("email", "User")),
        picture=user_data.get("picture", ""),
        session_token=session_token,
        google_access_token=access_token,
        refresh_token=refresh_token,
        expires_at=expires_at,
        granted_scopes=granted_scopes,
    )
    await upsert_user_with_token(session, creds)

    return to_user_response(creds)


async def fetch_profile_picture(google_access_token: str) -> str:
    if not google_access_token:
        return ""
    async with httpx.AsyncClient(timeout=10.0) as client:
        user_resp = await client.get(
            GOOGLE_USERINFO_URL,
            headers={"Authorization": f"Bearer {google_access_token}"},
        )
    if user_resp.status_code != 200:
        return ""
    return str(user_resp.json().get("picture") or "").strip()


async def refresh_access_token(
    session: AsyncSession, creds: StoredCredentials
) -> StoredCredentials:
    if not creds.refresh_token:
        raise ValueError("No refresh token available; please re-authenticate")

    client_id, client_secret = resolve_google_credentials()
    if not client_id or not client_secret:
        raise ValueError("Google OAuth is not configured")

    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(
            GOOGLE_TOKEN_URL,
            data={
                "client_id": client_id,
                "client_secret": client_secret,
                "refresh_token": creds.refresh_token,
                "grant_type": "refresh_token",
            },
        )
        if resp.status_code != 200:
            raise ValueError(f"Token refresh failed: {resp.text}")

        data = resp.json()

    new_access = data["access_token"]
    expires_in = int(data.get("expires_in", 3600))
    expires_at = int(time.time()) + expires_in
    scope_update = data.get("scope")

    updated = await update_google_access_token(
        session, creds.session_token, new_access, expires_at
    )
    if updated is None:
        raise ValueError("Failed to update stored credentials")
    if scope_update:
        updated.granted_scopes = scopes_to_string(scope_update.split())
        await upsert_user_with_token(session, updated)
    return updated


async def get_valid_credentials(
    session: AsyncSession, session_token: str
) -> StoredCredentials:
    creds = await get_credentials_by_access_token(session, session_token)
    if creds is None:
        raise ValueError("Invalid or expired session; please sign in again")

    if is_expired(creds.expires_at):
        creds = await refresh_access_token(session, creds)

    return creds

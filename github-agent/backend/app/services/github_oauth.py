import time

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.app_config import resolve_github_credentials
from app.models.auth import GitHubUserResponse
from app.services.auth_service import (
    StoredCredentials,
    get_credentials_by_access_token,
    is_expired,
    new_session_token,
    to_user_response,
    update_github_access_token,
    upsert_user_with_token,
)
from app.services.scope_registry import scopes_to_string

GITHUB_TOKEN_URL = "https://github.com/login/oauth/access_token"
GITHUB_AUTH_URL = "https://github.com/login/oauth/authorize"
GITHUB_USER_URL = "https://api.github.com/user"
GITHUB_EMAILS_URL = "https://api.github.com/user/emails"
GITHUB_OAUTH_REDIRECT_URI = "http://127.0.0.1:8000/auth/github/callback"
GITHUB_API_ACCEPT = "application/vnd.github+json"
NON_EXPIRING_TOKEN_TTL = 10 * 365 * 24 * 60 * 60

OAUTH_SCOPES = (
    "read:user",
    "user:email",
    "repo",
    "notifications",
)


def build_github_auth_url(client_id: str, state: str) -> str:
    from urllib.parse import urlencode

    params = {
        "client_id": client_id,
        "redirect_uri": GITHUB_OAUTH_REDIRECT_URI,
        "scope": " ".join(OAUTH_SCOPES),
        "state": state,
        "allow_signup": "true",
    }
    return f"{GITHUB_AUTH_URL}?{urlencode(params)}"


def _normalize_scope_string(raw: str) -> str:
    return scopes_to_string([part for part in raw.replace(",", " ").split() if part])


async def _primary_email(client: httpx.AsyncClient, access_token: str) -> str:
    resp = await client.get(
        GITHUB_EMAILS_URL,
        headers=_api_headers(access_token),
    )
    if resp.status_code != 200:
        return ""
    emails = resp.json()
    if not isinstance(emails, list):
        return ""
    for entry in emails:
        if isinstance(entry, dict) and entry.get("primary") and entry.get("email"):
            return str(entry["email"])
    for entry in emails:
        if isinstance(entry, dict) and entry.get("email"):
            return str(entry["email"])
    return ""


def _api_headers(access_token: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {access_token}",
        "Accept": GITHUB_API_ACCEPT,
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "github-agent",
    }


async def exchange_code(
    session: AsyncSession, code: str, redirect_uri: str
) -> GitHubUserResponse:
    client_id, client_secret = resolve_github_credentials()
    if not client_id or not client_secret:
        raise ValueError(
            "GitHub OAuth is not configured. Add credentials in Settings → GitHub OAuth."
        )

    async with httpx.AsyncClient(timeout=30.0) as client:
        token_resp = await client.post(
            GITHUB_TOKEN_URL,
            headers={"Accept": "application/json"},
            data={
                "code": code,
                "client_id": client_id,
                "client_secret": client_secret,
                "redirect_uri": redirect_uri,
            },
        )
        if token_resp.status_code != 200:
            raise ValueError(f"Token exchange failed: {token_resp.text}")

        token_data = token_resp.json()
        if token_data.get("error"):
            raise ValueError(token_data.get("error_description") or token_data["error"])

        access_token = token_data.get("access_token")
        if not access_token:
            raise ValueError("Token exchange failed: missing access_token")

        refresh_token = token_data.get("refresh_token", "") or ""
        expires_in = int(token_data.get("expires_in") or NON_EXPIRING_TOKEN_TTL)
        expires_at = int(time.time()) + expires_in
        granted_scopes = _normalize_scope_string(
            token_data.get("scope") or " ".join(OAUTH_SCOPES)
        )

        user_resp = await client.get(
            GITHUB_USER_URL,
            headers=_api_headers(access_token),
        )
        if user_resp.status_code != 200:
            raise ValueError(f"Userinfo fetch failed: {user_resp.text}")

        user_data = user_resp.json()
        email = str(user_data.get("email") or "").strip()
        if not email:
            email = await _primary_email(client, access_token)

    login = str(user_data.get("login") or "user")
    session_token = new_session_token()
    creds = StoredCredentials(
        user_id=str(user_data["id"]),
        email=email or f"{login}@users.noreply.github.com",
        name=str(user_data.get("name") or login),
        picture=str(user_data.get("avatar_url") or ""),
        session_token=session_token,
        github_access_token=access_token,
        refresh_token=refresh_token,
        expires_at=expires_at,
        granted_scopes=granted_scopes,
    )
    await upsert_user_with_token(session, creds)

    return to_user_response(creds)


async def fetch_profile_picture(github_access_token: str) -> str:
    if not github_access_token:
        return ""
    async with httpx.AsyncClient(timeout=10.0) as client:
        user_resp = await client.get(
            GITHUB_USER_URL,
            headers=_api_headers(github_access_token),
        )
    if user_resp.status_code != 200:
        return ""
    return str(user_resp.json().get("avatar_url") or "").strip()


async def refresh_access_token(
    session: AsyncSession, creds: StoredCredentials
) -> StoredCredentials:
    if not creds.refresh_token:
        raise ValueError("No refresh token available; please re-authenticate")

    client_id, client_secret = resolve_github_credentials()
    if not client_id or not client_secret:
        raise ValueError("GitHub OAuth is not configured")

    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(
            GITHUB_TOKEN_URL,
            headers={"Accept": "application/json"},
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
        if data.get("error"):
            raise ValueError(data.get("error_description") or data["error"])

    new_access = data.get("access_token")
    if not new_access:
        raise ValueError("Token refresh failed: missing access_token")
    expires_in = int(data.get("expires_in") or NON_EXPIRING_TOKEN_TTL)
    expires_at = int(time.time()) + expires_in
    scope_update = data.get("scope")

    updated = await update_github_access_token(
        session, creds.session_token, new_access, expires_at
    )
    if updated is None:
        raise ValueError("Failed to update stored credentials")
    if data.get("refresh_token"):
        updated.refresh_token = data["refresh_token"]
    if scope_update:
        updated.granted_scopes = _normalize_scope_string(scope_update)
        await upsert_user_with_token(session, updated)
    elif data.get("refresh_token"):
        await upsert_user_with_token(session, updated)
    return updated


async def get_valid_credentials(
    session: AsyncSession, session_token: str
) -> StoredCredentials:
    creds = await get_credentials_by_access_token(session, session_token)
    if creds is None:
        raise ValueError("Invalid or expired session; please sign in again")

    if is_expired(creds.expires_at):
        if creds.refresh_token:
            creds = await refresh_access_token(session, creds)
        else:
            raise ValueError("GitHub session expired; please sign in again")

    return creds

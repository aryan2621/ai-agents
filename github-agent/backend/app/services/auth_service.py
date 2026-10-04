import secrets
from dataclasses import dataclass
from datetime import datetime, timezone

from app.db.database import Store
from app.db.models import OAuthToken, User, UserSettings
from app.models.auth import GitHubUserResponse, PermissionStatusResponse
from app.services.scope_registry import (
    build_permission_statuses,
    effective_granted_scopes,
)
from app.services.token_crypto import decrypt_token, encrypt_token


@dataclass
class StoredCredentials:
    user_id: str
    email: str
    name: str
    picture: str
    session_token: str
    github_access_token: str
    refresh_token: str
    expires_at: int
    granted_scopes: str = ""


def is_expired(expires_at: int, buffer_seconds: int = 60) -> bool:
    if expires_at <= 0:
        return False
    now = int(datetime.now(timezone.utc).timestamp())
    return expires_at <= now + buffer_seconds


async def upsert_user_with_token(
    session: Store,
    creds: StoredCredentials,
) -> None:
    user = session.users.get(creds.user_id)
    if user is None:
        session.add(
            User(
                id=creds.user_id,
                email=creds.email,
                name=creds.name,
                picture=creds.picture,
            )
        )
    else:
        user.email = creds.email
        user.name = creds.name
        if creds.picture:
            user.picture = creds.picture

    token = session.tokens.get(creds.user_id)
    if token is None:
        session.add(
            OAuthToken(
                user_id=creds.user_id,
                access_token=creds.session_token,
                github_access_token=encrypt_token(creds.github_access_token),
                refresh_token=encrypt_token(creds.refresh_token),
                expires_at=creds.expires_at,
                granted_scopes=creds.granted_scopes,
            )
        )
    else:
        token.access_token = creds.session_token
        token.github_access_token = encrypt_token(creds.github_access_token)
        if creds.refresh_token:
            token.refresh_token = encrypt_token(creds.refresh_token)
        token.expires_at = creds.expires_at
        if creds.granted_scopes:
            token.granted_scopes = creds.granted_scopes

    if creds.user_id not in session.settings:
        session.add(UserSettings(user_id=creds.user_id))

    await session.commit()


def _find_by_session_token(session: Store, session_token: str) -> tuple[User, OAuthToken] | None:
    if not session_token:
        return None
    for token in session.tokens.values():
        if token.access_token == session_token:
            user = session.users.get(token.user_id)
            if user is not None:
                return user, token
    return None


def _credentials(user: User, token: OAuthToken) -> StoredCredentials:
    return StoredCredentials(
        user_id=user.id,
        email=user.email,
        name=user.name,
        picture=user.picture,
        session_token=token.access_token,
        github_access_token=decrypt_token(token.github_access_token),
        refresh_token=decrypt_token(token.refresh_token),
        expires_at=token.expires_at,
        granted_scopes=token.granted_scopes or "",
    )


async def get_credentials_by_access_token(
    session: Store, session_token: str
) -> StoredCredentials | None:
    found = _find_by_session_token(session, session_token)
    return _credentials(*found) if found else None


async def update_github_access_token(
    session: Store,
    session_token: str,
    github_access_token: str,
    expires_at: int,
) -> StoredCredentials | None:
    found = _find_by_session_token(session, session_token)
    if found is None:
        return None
    user, token = found
    token.github_access_token = encrypt_token(github_access_token)
    token.expires_at = expires_at
    await session.commit()
    return _credentials(user, token)


def new_session_token() -> str:
    return secrets.token_urlsafe(32)


def to_user_response(creds: StoredCredentials) -> GitHubUserResponse:
    granted = effective_granted_scopes(creds.granted_scopes)
    permissions = build_permission_statuses(granted)
    return GitHubUserResponse(
        id=creds.user_id,
        email=creds.email,
        name=creds.name,
        picture=creds.picture,
        accessToken=creds.session_token,
        expiresAt=creds.expires_at,
        grantedScopes=granted,
        permissions=[
            PermissionStatusResponse(
                id=p.id,
                label=p.label,
                scope=p.scope,
                granted=p.granted,
            )
            for p in permissions
        ],
    )


async def get_user_by_access_token(
    session: Store, access_token: str
) -> tuple[User, OAuthToken] | None:
    return _find_by_session_token(session, access_token)


async def delete_user_session(session: Store, access_token: str) -> None:
    found = _find_by_session_token(session, access_token)
    if found:
        await session.delete(found[1])
        await session.commit()

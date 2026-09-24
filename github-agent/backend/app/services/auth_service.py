import secrets
from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

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
    session: AsyncSession,
    creds: StoredCredentials,
) -> None:
    result = await session.execute(select(User).where(User.id == creds.user_id))
    user = result.scalar_one_or_none()
    if user is None:
        user = User(
            id=creds.user_id,
            email=creds.email,
            name=creds.name,
            picture=creds.picture,
        )
        session.add(user)
    else:
        user.email = creds.email
        user.name = creds.name
        if creds.picture:
            user.picture = creds.picture

    token_result = await session.execute(
        select(OAuthToken).where(OAuthToken.user_id == creds.user_id)
    )
    token = token_result.scalar_one_or_none()
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

    settings_result = await session.execute(
        select(UserSettings).where(UserSettings.user_id == creds.user_id)
    )
    if settings_result.scalar_one_or_none() is None:
        session.add(UserSettings(user_id=creds.user_id))

    await session.commit()


async def get_credentials_by_access_token(
    session: AsyncSession, session_token: str
) -> StoredCredentials | None:
    result = await session.execute(
        select(OAuthToken, User)
        .join(User, User.id == OAuthToken.user_id)
        .where(OAuthToken.access_token == session_token)
    )
    row = result.first()
    if row is None:
        return None
    token, user = row
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


async def update_github_access_token(
    session: AsyncSession,
    session_token: str,
    github_access_token: str,
    expires_at: int,
) -> StoredCredentials | None:
    result = await session.execute(
        select(OAuthToken, User)
        .join(User, User.id == OAuthToken.user_id)
        .where(OAuthToken.access_token == session_token)
    )
    row = result.first()
    if row is None:
        return None
    token, user = row
    token.github_access_token = encrypt_token(github_access_token)
    token.expires_at = expires_at
    await session.commit()
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
    session: AsyncSession, access_token: str
) -> tuple[User, OAuthToken] | None:
    result = await session.execute(
        select(User, OAuthToken)
        .join(OAuthToken, OAuthToken.user_id == User.id)
        .where(OAuthToken.access_token == access_token)
    )
    row = result.first()
    return row if row else None


async def delete_user_session(session: AsyncSession, access_token: str) -> None:
    result = await session.execute(
        select(OAuthToken).where(OAuthToken.access_token == access_token)
    )
    token = result.scalar_one_or_none()
    if token:
        await session.delete(token)
        await session.commit()

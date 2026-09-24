from datetime import datetime, timezone

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.constants.models import normalize_llm_model
from app.models.chat import ChatMessage
from app.db.models import Conversation, Message, User, UserSettings
from app.services.workspace.workspace_context import sanitize_workspace_context
from app.types.agents import INVALID_AGENT_ROOM, ROOM_AGENT_NAMES, is_room_agent

DEFAULT_AGENT_OVERRIDES = {name: {"enabled": True} for name in ROOM_AGENT_NAMES}


def _migrate_legacy_llm_settings(settings: UserSettings) -> bool:
    changed = False
    normalized = normalize_llm_model(settings.default_model)
    if normalized != settings.default_model:
        settings.default_model = normalized
        changed = True

    raw = dict(settings.agent_overrides or {})
    next_overrides: dict[str, dict] = {}
    for agent in ROOM_AGENT_NAMES:
        cfg = raw.get(agent)
        enabled = True
        if isinstance(cfg, dict):
            enabled = bool(cfg.get("enabled", True))
        next_overrides[agent] = {"enabled": enabled}

    if raw != next_overrides:
        settings.agent_overrides = next_overrides
        changed = True
    return changed


async def get_or_create_settings(session: AsyncSession, user_id: str) -> UserSettings:
    result = await session.execute(
        select(UserSettings).where(UserSettings.user_id == user_id)
    )
    settings = result.scalar_one_or_none()
    if settings is None:
        settings = UserSettings(user_id=user_id, agent_overrides=DEFAULT_AGENT_OVERRIDES.copy())
        session.add(settings)
        await session.commit()
        await session.refresh(settings)
    elif not settings.agent_overrides:
        settings.agent_overrides = DEFAULT_AGENT_OVERRIDES.copy()
        await session.commit()
    if _migrate_legacy_llm_settings(settings):
        await session.commit()
        await session.refresh(settings)
    return settings


async def _conversation_with_messages(
    session: AsyncSession, conv_id: str, user_id: str
) -> Conversation | None:
    result = await session.execute(
        select(Conversation)
        .where(Conversation.id == conv_id, Conversation.user_id == user_id)
        .options(selectinload(Conversation.messages))
    )
    return result.scalar_one_or_none()


async def list_conversations(session: AsyncSession, user_id: str) -> list[Conversation]:
    result = await session.execute(
        select(Conversation)
        .where(Conversation.user_id == user_id)
        .options(selectinload(Conversation.messages))
        .order_by(Conversation.updated_at.desc())
    )
    return list(result.scalars().all())


async def get_conversation(
    session: AsyncSession, user_id: str, conv_id: str
) -> Conversation | None:
    return await _conversation_with_messages(session, conv_id, user_id)


async def create_conversation(
    session: AsyncSession,
    user_id: str,
    conv_id: str,
    title: str = "New Chat",
    agent_filter: str = "",
) -> Conversation:
    if not is_room_agent(agent_filter):
        raise ValueError(INVALID_AGENT_ROOM)
    conv = Conversation(id=conv_id, user_id=user_id, title=title, agent_filter=agent_filter)
    session.add(conv)
    await session.commit()
    loaded = await _conversation_with_messages(session, conv_id, user_id)
    if loaded is None:
        raise RuntimeError(f"Failed to load conversation {conv_id} after create")
    return loaded


async def delete_conversation(session: AsyncSession, user_id: str, conv_id: str) -> bool:
    result = await session.execute(
        select(Conversation).where(
            Conversation.id == conv_id, Conversation.user_id == user_id
        )
    )
    conv = result.scalar_one_or_none()
    if conv is None:
        return False
    await session.delete(conv)
    await session.commit()
    return True


async def delete_conversations(
    session: AsyncSession, user_id: str, conv_ids: list[str]
) -> int:
    if not conv_ids:
        return 0
    unique_ids = list(dict.fromkeys(conv_ids))
    result = await session.execute(
        select(Conversation).where(
            Conversation.user_id == user_id,
            Conversation.id.in_(unique_ids),
        )
    )
    convs = result.scalars().all()
    for conv in convs:
        await session.delete(conv)
    await session.commit()
    return len(convs)


async def delete_all_conversations(session: AsyncSession, user_id: str) -> None:
    result = await session.execute(
        select(Conversation).where(Conversation.user_id == user_id)
    )
    for conv in result.scalars().all():
        await session.delete(conv)
    await session.commit()


async def rename_conversation(
    session: AsyncSession, user_id: str, conv_id: str, title: str
) -> Conversation | None:
    result = await session.execute(
        select(Conversation).where(
            Conversation.id == conv_id, Conversation.user_id == user_id
        )
    )
    conv = result.scalar_one_or_none()
    if conv is None:
        return None
    conv.title = title
    conv.updated_at = datetime.now(timezone.utc)
    await session.commit()
    loaded = await _conversation_with_messages(session, conv_id, user_id)
    return loaded


async def get_conversation_history(
    session: AsyncSession, user_id: str, conv_id: str, limit: int = 20
) -> list[ChatMessage]:
    conv = await _conversation_with_messages(session, conv_id, user_id)
    if conv is None:
        return []
    messages = conv.messages[-limit:]
    return [
        ChatMessage(
            role=m.role,  # type: ignore[arg-type]
            content=m.content,
            agent_name=m.agent_name,
        )
        for m in messages
        if m.role in ("user", "assistant", "system")
    ]


async def get_workspace_context(
    session: AsyncSession, user_id: str, conv_id: str
) -> dict[str, str]:
    result = await session.execute(
        select(Conversation.workspace_context).where(
            Conversation.id == conv_id, Conversation.user_id == user_id
        )
    )
    raw = result.scalar_one_or_none()
    if not isinstance(raw, dict):
        return {}
    return sanitize_workspace_context({str(k): str(v) for k, v in raw.items() if v})


async def merge_workspace_context(
    session: AsyncSession, user_id: str, conv_id: str, updates: dict[str, str]
) -> dict[str, str]:
    if not updates:
        return await get_workspace_context(session, user_id, conv_id)

    result = await session.execute(
        select(Conversation).where(
            Conversation.id == conv_id, Conversation.user_id == user_id
        )
    )
    conv = result.scalar_one_or_none()
    if conv is None:
        return {}

    merged = sanitize_workspace_context(conv.workspace_context)
    merged.update(sanitize_workspace_context(updates))
    conv.workspace_context = merged
    conv.updated_at = datetime.now(timezone.utc)
    await session.commit()
    return {str(k): str(v) for k, v in merged.items() if v}


async def update_agent_filter(
    session: AsyncSession, user_id: str, conv_id: str, agent_filter: str
) -> Conversation | None:
    result = await session.execute(
        select(Conversation).where(
            Conversation.id == conv_id, Conversation.user_id == user_id
        )
    )
    conv = result.scalar_one_or_none()
    if conv is None:
        return None
    conv.agent_filter = agent_filter
    conv.updated_at = datetime.now(timezone.utc)
    await session.commit()
    return await _conversation_with_messages(session, conv_id, user_id)


async def add_message(
    session: AsyncSession,
    user_id: str,
    conv_id: str,
    msg_id: str,
    role: str,
    content: str,
    agent_name: str | None = None,
) -> Message | None:
    result = await session.execute(
        select(Conversation).where(
            Conversation.id == conv_id, Conversation.user_id == user_id
        )
    )
    conv = result.scalar_one_or_none()
    if conv is None:
        return None

    existing = await session.execute(
        select(Message).where(
            Message.id == msg_id,
            Message.conversation_id == conv_id,
        )
    )
    existing_msg = existing.scalar_one_or_none()
    conv.updated_at = datetime.now(timezone.utc)
    if existing_msg is not None:
        existing_msg.content = content
        if agent_name is not None:
            existing_msg.agent_name = agent_name
        await session.commit()
        await session.refresh(existing_msg)
        return existing_msg

    msg = Message(
        id=msg_id,
        conversation_id=conv_id,
        role=role,
        content=content,
        agent_name=agent_name,
    )
    conv.updated_at = datetime.now(timezone.utc)
    session.add(msg)
    await session.commit()
    await session.refresh(msg)
    return msg


async def edit_user_message_and_truncate(
    session: AsyncSession,
    user_id: str,
    conv_id: str,
    msg_id: str,
    content: str,
) -> Conversation | None:
    conv = await _conversation_with_messages(session, conv_id, user_id)
    if conv is None:
        return None

    ordered = sorted(conv.messages, key=lambda m: (m.timestamp, m.id))
    target_idx: int | None = None
    for idx, message in enumerate(ordered):
        if message.id == msg_id:
            if message.role != "user":
                return None
            target_idx = idx
            break

    if target_idx is None:
        return None

    target = ordered[target_idx]
    target.content = content
    ids_to_delete = [m.id for m in ordered[target_idx + 1 :]]
    if ids_to_delete:
        await session.execute(delete(Message).where(Message.id.in_(ids_to_delete)))

    conv.updated_at = datetime.now(timezone.utc)
    await session.commit()
    session.expire(conv, ["messages"])
    return await _conversation_with_messages(session, conv_id, user_id)


async def update_message(
    session: AsyncSession,
    user_id: str,
    conv_id: str,
    msg_id: str,
    content: str,
    agent_name: str | None = None,
) -> Message | None:
    result = await session.execute(
        select(Message)
        .join(Conversation, Conversation.id == Message.conversation_id)
        .where(
            Message.id == msg_id,
            Message.conversation_id == conv_id,
            Conversation.user_id == user_id,
        )
    )
    msg = result.scalar_one_or_none()
    if msg is None:
        return None
    msg.content = content
    if agent_name:
        msg.agent_name = agent_name
    conv_result = await session.execute(
        select(Conversation).where(Conversation.id == conv_id)
    )
    conv = conv_result.scalar_one()
    conv.updated_at = datetime.now(timezone.utc)
    await session.commit()
    await session.refresh(msg)
    return msg

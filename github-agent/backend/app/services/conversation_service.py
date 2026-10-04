from datetime import datetime, timedelta, timezone

from app.constants.models import normalize_llm_model
from app.db.database import Store
from app.db.models import Conversation, Message, UserSettings
from app.models.chat import ChatMessage
from app.services.workspace_context import (
    merge_workspace_context as merge_maps,
    sanitize_workspace_context,
)
from app.types.agents import INVALID_AGENT_ROOM, ROOM_AGENT_NAMES, is_room_agent

DEFAULT_AGENT_OVERRIDES = {name: {"enabled": True} for name in ROOM_AGENT_NAMES}


def _now() -> datetime:
    return datetime.now(timezone.utc)


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


async def get_or_create_settings(session: Store, user_id: str) -> UserSettings:
    settings = session.settings.get(user_id)
    if settings is None:
        settings = UserSettings(user_id=user_id, agent_overrides=DEFAULT_AGENT_OVERRIDES.copy())
        session.add(settings)
        await session.commit()
    elif not settings.agent_overrides:
        settings.agent_overrides = DEFAULT_AGENT_OVERRIDES.copy()
        await session.commit()
    if _migrate_legacy_llm_settings(settings):
        await session.commit()
    return settings


def _owned(session: Store, conv_id: str, user_id: str) -> Conversation | None:
    conv = session.conversations.get(conv_id)
    return conv if conv is not None and conv.user_id == user_id else None


# A chat is saved with its first message; one still empty after this long was never used (from
# before that, or a send that failed), so it's dropped instead of cluttering the list.
EMPTY_CHAT_MAX_AGE = timedelta(minutes=10)


async def list_conversations(session: Store, user_id: str) -> list[Conversation]:
    owned = [c for c in session.conversations.values() if c.user_id == user_id]
    cutoff = _now() - EMPTY_CHAT_MAX_AGE
    unused = [c for c in owned if not c.messages and c.created_at < cutoff]
    if unused:
        for conv in unused:
            await session.delete(conv)
        await session.commit()
        owned = [c for c in owned if c not in unused]
    return sorted(owned, key=lambda c: c.updated_at, reverse=True)


async def get_conversation(session: Store, user_id: str, conv_id: str) -> Conversation | None:
    return _owned(session, conv_id, user_id)


async def create_conversation(
    session: Store,
    user_id: str,
    conv_id: str,
    title: str = "New Chat",
    agent_filter: str = "",
) -> Conversation:
    if not is_room_agent(agent_filter):
        raise ValueError(INVALID_AGENT_ROOM)
    if conv_id in session.conversations:
        raise ValueError(f"Conversation {conv_id} already exists")
    conv = Conversation(id=conv_id, user_id=user_id, title=title, agent_filter=agent_filter)
    session.add(conv)
    await session.commit()
    return conv


async def delete_conversation(session: Store, user_id: str, conv_id: str) -> bool:
    conv = _owned(session, conv_id, user_id)
    if conv is None:
        return False
    await session.delete(conv)
    await session.commit()
    return True


async def delete_conversations(session: Store, user_id: str, conv_ids: list[str]) -> int:
    if not conv_ids:
        return 0
    convs = [c for c in (_owned(session, i, user_id) for i in dict.fromkeys(conv_ids)) if c]
    for conv in convs:
        await session.delete(conv)
    await session.commit()
    return len(convs)


async def delete_all_conversations(session: Store, user_id: str) -> None:
    for conv in [c for c in session.conversations.values() if c.user_id == user_id]:
        await session.delete(conv)
    await session.commit()


async def rename_conversation(
    session: Store, user_id: str, conv_id: str, title: str
) -> Conversation | None:
    conv = _owned(session, conv_id, user_id)
    if conv is None:
        return None
    conv.title = title
    conv.updated_at = _now()
    await session.commit()
    return conv


async def get_conversation_history(
    session: Store, user_id: str, conv_id: str, limit: int = 20
) -> list[ChatMessage]:
    conv = _owned(session, conv_id, user_id)
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


async def get_workspace_context(session: Store, user_id: str, conv_id: str) -> dict[str, str]:
    conv = _owned(session, conv_id, user_id)
    raw = conv.workspace_context if conv is not None else None
    if not isinstance(raw, dict):
        return {}
    return sanitize_workspace_context({str(k): str(v) for k, v in raw.items() if v})


async def merge_workspace_context(
    session: Store, user_id: str, conv_id: str, updates: dict[str, str]
) -> dict[str, str]:
    if not updates:
        return await get_workspace_context(session, user_id, conv_id)

    conv = _owned(session, conv_id, user_id)
    if conv is None:
        return {}

    merged = merge_maps(conv.workspace_context, updates)
    conv.workspace_context = merged
    conv.updated_at = _now()
    await session.commit()
    return {str(k): str(v) for k, v in merged.items() if v}


async def add_message(
    session: Store,
    user_id: str,
    conv_id: str,
    msg_id: str,
    role: str,
    content: str,
    agent_name: str | None = None,
) -> Message | None:
    conv = _owned(session, conv_id, user_id)
    if conv is None:
        return None

    conv.updated_at = _now()
    existing_msg = next((m for m in conv.messages if m.id == msg_id), None)
    if existing_msg is not None:
        existing_msg.content = content
        if agent_name is not None:
            existing_msg.agent_name = agent_name
        await session.commit()
        return existing_msg

    msg = Message(
        id=msg_id,
        conversation_id=conv_id,
        role=role,
        content=content,
        agent_name=agent_name,
    )
    session.add(msg)
    await session.commit()
    return msg


async def edit_user_message_and_truncate(
    session: Store,
    user_id: str,
    conv_id: str,
    msg_id: str,
    content: str,
) -> Conversation | None:
    conv = _owned(session, conv_id, user_id)
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

    ordered[target_idx].content = content
    conv.messages = ordered[: target_idx + 1]
    conv.updated_at = _now()
    await session.commit()
    return conv


async def update_message(
    session: Store,
    user_id: str,
    conv_id: str,
    msg_id: str,
    content: str,
    agent_name: str | None = None,
) -> Message | None:
    conv = _owned(session, conv_id, user_id)
    if conv is None:
        return None
    msg = next((m for m in conv.messages if m.id == msg_id), None)
    if msg is None:
        return None
    msg.content = content
    if agent_name:
        msg.agent_name = agent_name
    conv.updated_at = _now()
    await session.commit()
    return msg

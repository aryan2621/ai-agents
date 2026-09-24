from datetime import datetime

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.db.models import Conversation
from app.models.chat import LLMSettings
from app.services.conversation_service import (
    add_message,
    create_conversation,
    delete_all_conversations,
    delete_conversation,
    delete_conversations,
    edit_user_message_and_truncate,
    get_conversation,
    get_or_create_settings,
    list_conversations,
    rename_conversation,
    update_message,
)
from app.services.title_service import generate_conversation_title
from app.types.agents import INVALID_AGENT_ROOM, ROOM_AGENT_NAMES

router = APIRouter(prefix="/conversations", tags=["conversations"])


def _extract_bearer(authorization: str | None) -> str:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")
    return authorization[7:]


async def _get_user_id(session: AsyncSession, access_token: str) -> str:
    from app.services.auth_service import get_user_by_access_token

    row = await get_user_by_access_token(session, access_token)
    if row is None:
        raise HTTPException(status_code=401, detail="Invalid session")
    return row[0].id


class MessageOut(BaseModel):
    id: str
    role: str
    content: str
    agentName: str | None = None
    timestamp: datetime


class ConversationOut(BaseModel):
    id: str
    title: str
    messages: list[MessageOut]
    createdAt: datetime
    updatedAt: datetime
    agentFilter: str | None = None


class CreateConversationRequest(BaseModel):
    id: str
    title: str = "New Chat"
    agentFilter: str


class RenameRequest(BaseModel):
    title: str


class CreateMessageRequest(BaseModel):
    id: str
    role: str
    content: str
    agentName: str | None = None


class UpdateMessageRequest(BaseModel):
    content: str
    agentName: str | None = None


class EditMessageRequest(BaseModel):
    content: str


class GenerateTitleRequest(BaseModel):
    message: str
    settings: LLMSettings | None = None


def _conv_to_out(conv: Conversation) -> ConversationOut:
    return ConversationOut(
        id=conv.id,
        title=conv.title,
        agentFilter=conv.agent_filter,
        createdAt=conv.created_at,
        updatedAt=conv.updated_at,
        messages=[
            MessageOut(
                id=m.id,
                role=m.role,
                content=m.content,
                agentName=m.agent_name,
                timestamp=m.timestamp,
            )
            for m in conv.messages
        ],
    )


@router.get("", response_model=list[ConversationOut])
async def get_conversations(
    authorization: str | None = Header(default=None),
    session: AsyncSession = Depends(get_db),
) -> list[ConversationOut]:
    token = _extract_bearer(authorization)
    user_id = await _get_user_id(session, token)
    convs = await list_conversations(session, user_id)
    return [_conv_to_out(c) for c in convs]


@router.get("/{conv_id}", response_model=ConversationOut)
async def get_conversation_route(
    conv_id: str,
    authorization: str | None = Header(default=None),
    session: AsyncSession = Depends(get_db),
) -> ConversationOut:
    token = _extract_bearer(authorization)
    user_id = await _get_user_id(session, token)
    conv = await get_conversation(session, user_id, conv_id)
    if conv is None:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return _conv_to_out(conv)


@router.post("", response_model=ConversationOut)
async def post_conversation(
    body: CreateConversationRequest,
    authorization: str | None = Header(default=None),
    session: AsyncSession = Depends(get_db),
) -> ConversationOut:
    token = _extract_bearer(authorization)
    user_id = await _get_user_id(session, token)
    if body.agentFilter not in ROOM_AGENT_NAMES:
        raise HTTPException(status_code=400, detail=INVALID_AGENT_ROOM)
    try:
        conv = await create_conversation(
            session, user_id, body.id, body.title, body.agentFilter
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return _conv_to_out(conv)


@router.patch("/{conv_id}", response_model=ConversationOut)
async def patch_conversation(
    conv_id: str,
    body: RenameRequest,
    authorization: str | None = Header(default=None),
    session: AsyncSession = Depends(get_db),
):
    token = _extract_bearer(authorization)
    user_id = await _get_user_id(session, token)
    conv = await rename_conversation(session, user_id, conv_id, body.title)
    if conv is None:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return _conv_to_out(conv)


class BulkDeleteRequest(BaseModel):
    ids: list[str]


@router.post("/bulk-delete")
async def bulk_delete_conversations(
    body: BulkDeleteRequest,
    authorization: str | None = Header(default=None),
    session: AsyncSession = Depends(get_db),
):
    token = _extract_bearer(authorization)
    user_id = await _get_user_id(session, token)
    deleted = await delete_conversations(session, user_id, body.ids)
    return {"status": "ok", "deleted": deleted}


@router.delete("/{conv_id}")
async def remove_conversation(
    conv_id: str,
    authorization: str | None = Header(default=None),
    session: AsyncSession = Depends(get_db),
):
    token = _extract_bearer(authorization)
    user_id = await _get_user_id(session, token)
    ok = await delete_conversation(session, user_id, conv_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return {"status": "ok"}


@router.delete("")
async def remove_all_conversations(
    authorization: str | None = Header(default=None),
    session: AsyncSession = Depends(get_db),
):
    token = _extract_bearer(authorization)
    user_id = await _get_user_id(session, token)
    await delete_all_conversations(session, user_id)
    return {"status": "ok"}


@router.post("/{conv_id}/messages", response_model=MessageOut)
async def post_message(
    conv_id: str,
    body: CreateMessageRequest,
    authorization: str | None = Header(default=None),
    session: AsyncSession = Depends(get_db),
):
    token = _extract_bearer(authorization)
    user_id = await _get_user_id(session, token)
    msg = await add_message(
        session, user_id, conv_id, body.id, body.role, body.content, body.agentName
    )
    if msg is None:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return MessageOut(
        id=msg.id,
        role=msg.role,
        content=msg.content,
        agentName=msg.agent_name,
        timestamp=msg.timestamp,
    )


@router.patch("/{conv_id}/messages/{msg_id}", response_model=MessageOut)
async def patch_message(
    conv_id: str,
    msg_id: str,
    body: UpdateMessageRequest,
    authorization: str | None = Header(default=None),
    session: AsyncSession = Depends(get_db),
):
    token = _extract_bearer(authorization)
    user_id = await _get_user_id(session, token)
    msg = await update_message(
        session, user_id, conv_id, msg_id, body.content, body.agentName
    )
    if msg is None:
        raise HTTPException(status_code=404, detail="Message not found")
    return MessageOut(
        id=msg.id,
        role=msg.role,
        content=msg.content,
        agentName=msg.agent_name,
        timestamp=msg.timestamp,
    )


@router.post("/{conv_id}/messages/{msg_id}/edit", response_model=ConversationOut)
async def edit_message_and_truncate(
    conv_id: str,
    msg_id: str,
    body: EditMessageRequest,
    authorization: str | None = Header(default=None),
    session: AsyncSession = Depends(get_db),
):
    token = _extract_bearer(authorization)
    user_id = await _get_user_id(session, token)
    conv = await edit_user_message_and_truncate(
        session, user_id, conv_id, msg_id, body.content
    )
    if conv is None:
        raise HTTPException(status_code=404, detail="Message or conversation not found")
    return _conv_to_out(conv)


@router.post("/{conv_id}/generate-title", response_model=ConversationOut)
async def generate_conversation_title_route(
    conv_id: str,
    body: GenerateTitleRequest,
    authorization: str | None = Header(default=None),
    session: AsyncSession = Depends(get_db),
):
    token = _extract_bearer(authorization)
    user_id = await _get_user_id(session, token)
    user_settings = await get_or_create_settings(session, user_id)
    from app.services.llm_keys import apply_keys_to_llm_settings

    settings = apply_keys_to_llm_settings(body.settings, user_settings)
    title = await generate_conversation_title(body.message, settings)
    conv = await rename_conversation(session, user_id, conv_id, title)
    if conv is None:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return _conv_to_out(conv)

import logging
import re

from langchain_core.messages import HumanMessage, SystemMessage

from app.constants.models import ROUTER_MAX_TOKENS
from app.graph.llm import build_chat_model
from app.models.chat import LLMSettings

logger = logging.getLogger(__name__)

TITLE_PROMPT = """You write short conversation titles for a Google Workspace AI assistant chat.
Output ONLY the title text — no quotes, no punctuation at the end, no explanation.
Use 3–6 words when possible. Max 60 characters. Be specific to the user's request."""


def _fallback_title(message: str) -> str:
    words = message.strip().split()
    if not words:
        return "New Chat"
    snippet = " ".join(words[:6])
    return snippet[:80]


def _sanitize_title(raw: str) -> str:
    title = raw.strip().strip('"\'').strip()
    title = re.sub(r"^title:\s*", "", title, flags=re.I)
    title = title.split("\n")[0].strip()
    if title.endswith("."):
        title = title[:-1].strip()
    if not title or title.lower() == "new chat":
        return ""
    return title[:80]


async def generate_conversation_title(message: str, settings: LLMSettings | None) -> str:
    message = message.strip()
    if not message:
        return _fallback_title(message)

    model = build_chat_model(
        settings,
        temperature_override=0.3,
        max_tokens_override=min(ROUTER_MAX_TOKENS, 48),
        validate_model_on_init=False,
    )

    try:
        raw = await model.ainvoke([
            SystemMessage(content=TITLE_PROMPT),
            HumanMessage(content=message[:500]),
        ])
        content = raw.content if isinstance(raw.content, str) else str(raw.content)
        title = _sanitize_title(content)
        if title:
            return title
    except Exception:
        logger.exception("LLM title generation failed")

    return _fallback_title(message)

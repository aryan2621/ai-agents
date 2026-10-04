import logging
import re

from langchain_core.messages import AIMessage, HumanMessage

from app.graph.llm import build_chat_model, ensure_model_running
from app.models.chat import LLMSettings

logger = logging.getLogger(__name__)


# The request goes in the user turn, not a system prompt: given a list of rules as a system
# prompt, Gemma writes out its plan ("User message: ... Constraint 1: ...") instead of a title.
def _title_request(message: str) -> str:
    return (
        "Write a short title (3 to 6 words) for a chat that starts with this message:\n\n"
        f"{message}\n\nReply with the title only."
    )


TITLE_EXAMPLES = [
    ("Show open pull requests that need my review in aryan2621/desktop-apps", "PRs awaiting my review"),
    ("why is the CI failing on main?", "Failing CI on main"),
]


def _fallback_title(message: str) -> str:
    words = message.strip().split()
    if not words:
        return "New Chat"
    snippet = " ".join(words[:6])
    return snippet[:80]


def _sanitize_title(raw: str, message: str = "") -> str:
    """The first line that looks like a title, without the list markers, labels or quotes a
    model sometimes adds, skipping lines that just echo the message. Empty if there is none, or
    if the model wrote out its reasoning ("User message: ...") instead of answering."""
    if re.search(r"^\W*user message\s*:", raw, flags=re.I | re.M):
        return ""
    for line in raw.splitlines():
        title = line.strip()
        title = re.sub(r"^[\s*#>\-•\d.)]+", "", title)  # bullets, headings, numbering
        title = title.replace("**", "").replace("`", "")
        title = re.sub(r"^(title|chat title|input|user|message)\s*:\s*", "", title, flags=re.I)
        title = title.strip().strip('"\'“”').strip()
        if title.endswith("."):
            title = title[:-1].strip()
        if not title or title.lower() == "new chat":
            continue
        if message and title.lower().strip("?!. ") == message.lower().strip("?!. "):
            continue  # an echo of the message, not a title
        return title[:80]
    return ""


async def generate_conversation_title(message: str, settings: LLMSettings | None) -> str:
    message = message.strip()
    if not message:
        return _fallback_title(message)

    try:
        await ensure_model_running(settings)
        model = build_chat_model(settings, temperature=0.3, max_tokens=48)
        prompt: list = []
        for example, title in TITLE_EXAMPLES:
            prompt += [HumanMessage(content=_title_request(example)), AIMessage(content=title)]
        prompt.append(HumanMessage(content=_title_request(message[:500])))
        raw = await model.ainvoke(prompt)
        content = raw.content if isinstance(raw.content, str) else str(raw.content)
        title = _sanitize_title(content, message)
        if title:
            return title
    except Exception:
        logger.exception("LLM title generation failed")

    return _fallback_title(message)

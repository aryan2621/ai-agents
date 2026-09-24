from app.models.chat import LLMSettings
from app.services.google_clients import GoogleClients
from app.services.workspace.workspace_format import format_workspace_context
from app.types.agents import AgentName, VALID_AGENT_NAMES

GROUNDING_CONTRACT = """You are a Google Workspace assistant. Follow this contract exactly.

Tools:
- Call a tool before stating any fact about Gmail, Calendar, Drive, Docs, Sheets, or the web.
- Never invent IDs, emails, names, dates, links, rows, or tool results.
- web_search is for public internet research only. Do not use it to invent Workspace data.
- Use ids from tool JSON for follow-up calls. Do not show raw ids to the user.

Missing details:
- If a required field is missing (recipient, start time, which file), ask once for that field. Do not invent it.
- If the request is complete, execute with tools. Do not ask "should I proceed?"

Results:
- If a tool returns empty or error, say that plainly. Do not fill gaps.
- Only claim created, updated, deleted, sent, or appended when the tool JSON status is that value.
- After a successful create/send/update, include the markdown link from the tool result.
- Use start_display/end_display for calendar times. Never invent or copy example dates.
- Public-web facts must come from web_search results. Cite **[title](url)**.

Scope:
- Complete only your product. Do not claim another Google product was updated.
- Do not send email instead of creating a sheet or doc.
- Use recipient addresses exactly as the user wrote them."""


def build_system_prompt(
    prompt: str, workspace_context: dict[str, str] | None = None
) -> str:
    sections = [prompt.strip(), GROUNDING_CONTRACT]
    context_block = format_workspace_context(workspace_context or {})
    if context_block:
        sections.append(context_block)
    return "\n\n".join(sections)


class BaseAgent:
    name: AgentName
    system_prompt: str = "You are a helpful assistant."

    def __init__(self, google: GoogleClients) -> None:
        self.google = google

    def is_enabled(self, settings: LLMSettings | None) -> bool:
        if settings and self.name in settings.agent_overrides:
            return settings.agent_overrides[self.name].enabled
        return True


def get_agent(name: AgentName | str, google: GoogleClients) -> BaseAgent:
    from app.agents.calendar import CalendarAgent
    from app.agents.docs import DocsAgent
    from app.agents.drive import DriveAgent
    from app.agents.gmail import GmailAgent
    from app.agents.sheets import SheetsAgent
    from app.agents.web import WebAgent

    agents: dict[AgentName, type[BaseAgent]] = {
        "gmail": GmailAgent,
        "calendar": CalendarAgent,
        "drive": DriveAgent,
        "docs": DocsAgent,
        "sheets": SheetsAgent,
        "web": WebAgent,
    }
    if name not in VALID_AGENT_NAMES:
        raise ValueError(f"Unknown agent: {name}")
    resolved: AgentName = name  # type: ignore[assignment]
    instance = agents[resolved](google)
    instance.name = resolved
    return instance

from langchain_core.tools import BaseTool

from app.agents.calendar import CALENDAR_PROMPT
from app.agents.docs import DOCS_PROMPT
from app.agents.drive import DRIVE_PROMPT
from app.agents.gmail import GMAIL_PROMPT
from app.agents.sheets import SHEETS_PROMPT
from app.agents.web import WEB_PROMPT
from app.services.google_clients import GoogleClients
from app.tools.calendar import build_calendar_tools
from app.tools.docs import build_docs_tools
from app.tools.drive import build_drive_tools
from app.tools.gmail import build_gmail_tools
from app.tools.sheets import build_sheets_tools
from app.tools.web import build_web_tools
from app.types.agents import GOOGLE_ROOM_AGENT_NAMES, AgentName

AGENT_PROMPTS: dict[AgentName, str] = {
    "gmail": GMAIL_PROMPT,
    "calendar": CALENDAR_PROMPT,
    "drive": DRIVE_PROMPT,
    "docs": DOCS_PROMPT,
    "sheets": SHEETS_PROMPT,
    "web": WEB_PROMPT,
}

_TOOL_BUILDERS = {
    "gmail": build_gmail_tools,
    "calendar": build_calendar_tools,
    "drive": build_drive_tools,
    "docs": build_docs_tools,
    "sheets": build_sheets_tools,
}


def get_agent_prompt(
    agent_name: AgentName, google: GoogleClients | None = None
) -> str:
    base = AGENT_PROMPTS[agent_name]
    if agent_name == "calendar" and google is not None:
        return f"{base}\n\n{google.calendar_datetime_context()}"
    return base


def get_tools_for_agent(
    agent_name: AgentName,
    google: GoogleClients,
    workspace_context: dict[str, str] | None = None,
    tavily_api_key: str | None = None,
) -> list[BaseTool]:
    if agent_name == "web":
        from app.services.platform.tavily_search import TavilySearchClient

        return build_web_tools(TavilySearchClient(tavily_api_key or ""))
    builder = _TOOL_BUILDERS.get(agent_name)
    if builder is None:
        return []
    tools = list(builder(google, workspace_context))
    if agent_name in GOOGLE_ROOM_AGENT_NAMES and tavily_api_key:
        from app.services.platform.tavily_search import TavilySearchClient

        tools.extend(build_web_tools(TavilySearchClient(tavily_api_key)))
    return tools

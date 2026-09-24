from langchain_core.tools import BaseTool

from app.agents.code import CODE_PROMPT
from app.agents.issues import ISSUES_PROMPT
from app.agents.notifications import NOTIFICATIONS_PROMPT
from app.agents.pulls import PULLS_PROMPT
from app.agents.repos import REPOS_PROMPT
from app.agents.web import WEB_PROMPT
from app.services.github_clients import GitHubClients
from app.tools.code import build_code_tools
from app.tools.issues import build_issues_tools
from app.tools.notifications import build_notifications_tools
from app.tools.pulls import build_pulls_tools
from app.tools.repos import build_repos_tools
from app.tools.web import build_web_tools
from app.types.agents import GITHUB_ROOM_AGENT_NAMES, AgentName

AGENT_PROMPTS: dict[AgentName, str] = {
    "repos": REPOS_PROMPT,
    "issues": ISSUES_PROMPT,
    "pulls": PULLS_PROMPT,
    "code": CODE_PROMPT,
    "notifications": NOTIFICATIONS_PROMPT,
    "web": WEB_PROMPT,
}

_TOOL_BUILDERS = {
    "repos": build_repos_tools,
    "issues": build_issues_tools,
    "pulls": build_pulls_tools,
    "code": build_code_tools,
    "notifications": build_notifications_tools,
}


def get_agent_prompt(
    agent_name: AgentName, github: GitHubClients | None = None
) -> str:
    del github
    return AGENT_PROMPTS[agent_name]


def get_tools_for_agent(
    agent_name: AgentName,
    github: GitHubClients,
    workspace_context: dict[str, str] | None = None,
    tavily_api_key: str | None = None,
) -> list[BaseTool]:
    if agent_name == "web":
        from app.services.tavily_search import TavilySearchClient

        return build_web_tools(TavilySearchClient(tavily_api_key or ""))
    builder = _TOOL_BUILDERS.get(agent_name)
    if builder is None:
        return []
    tools = list(builder(github, workspace_context))
    if agent_name in GITHUB_ROOM_AGENT_NAMES and tavily_api_key:
        from app.services.tavily_search import TavilySearchClient

        tools.extend(build_web_tools(TavilySearchClient(tavily_api_key)))
    return tools

from app.models.chat import LLMSettings
from app.services.github_clients import GitHubClients
from app.services.workspace_format import format_workspace_context
from app.types.agents import AgentName, VALID_AGENT_NAMES

GROUNDING_CONTRACT = """You are a GitHub assistant. Follow this contract exactly.

Tools:
- Call a tool before stating any fact about repositories, issues, pull requests, files, commits, notifications, or the web.
- A new user request is a new lookup. Call a tool even when ACTIVE WORKSPACE already has a list from a previous query.
- Never invent owners, repos, issue numbers, PR numbers, SHAs, links, empty results, or tool results.
- web_search is for public internet research only. Do not use it to invent GitHub data.
- Use owner, repo, and numbers from tool JSON for follow-up calls. Do not show raw ids to the user.

Missing details:
- If a required field is missing (which repo, issue number, branch names), ask once for that field. Do not invent it.
- If the request is complete, execute with tools. Do not ask "should I proceed?"

Results:
- Write the user-facing reply in the same language as the latest user message.
- If a tool returns empty or error, say that plainly. Do not fill gaps.
- Only claim created, updated, merged, or commented when the tool JSON status is that value.
- After a successful create/update/merge, include the markdown link from the tool result.
- Public-web facts must come from web_search results. Cite **[title](url)**.

Scope:
- Complete only GitHub actions. Do not claim other products were updated."""


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

    def __init__(self, github: GitHubClients) -> None:
        self.github = github

    def is_enabled(self, settings: LLMSettings | None) -> bool:
        if settings and self.name in settings.agent_overrides:
            return settings.agent_overrides[self.name].enabled
        return True


def get_agent(name: AgentName | str, github: GitHubClients) -> BaseAgent:
    from app.agents.code import CodeAgent
    from app.agents.issues import IssuesAgent
    from app.agents.notifications import NotificationsAgent
    from app.agents.pulls import PullsAgent
    from app.agents.repos import ReposAgent
    from app.agents.web import WebAgent

    agents: dict[AgentName, type[BaseAgent]] = {
        "repos": ReposAgent,
        "issues": IssuesAgent,
        "pulls": PullsAgent,
        "code": CodeAgent,
        "notifications": NotificationsAgent,
        "web": WebAgent,
    }
    if name not in VALID_AGENT_NAMES:
        raise ValueError(f"Unknown agent: {name}")
    resolved: AgentName = name  # type: ignore[assignment]
    instance = agents[resolved](github)
    instance.name = resolved
    return instance

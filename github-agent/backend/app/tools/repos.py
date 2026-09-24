from langchain_core.tools import BaseTool, tool

from app.services.github_clients import GitHubClients
from app.tools._errors import wrap_github_tool


def build_repos_tools(
    github: GitHubClients, workspace_context: dict[str, str] | None = None
) -> list[BaseTool]:
    g = github
    ctx = workspace_context or {}

    def _owner_default() -> str:
        return ctx.get("owner") or ""

    def _repo_default() -> str:
        return ctx.get("repo") or ""

    @tool
    def list_my_repos(max_results: int = 10) -> str:
        """List repositories the signed-in GitHub user can access, newest first."""
        return wrap_github_tool(g.list_my_repos, "list_my_repos")(max_results=max_results)

    @tool
    def get_repo(owner: str = "", repo: str = "") -> str:
        """Get one repository from list/search or the active repo in this chat."""
        return wrap_github_tool(g.get_repo, "get_repo")(
            owner=owner or _owner_default(),
            repo=repo or _repo_default(),
        )

    @tool
    def search_my_repos(query: str, max_results: int = 10) -> str:
        """Search the signed-in user's repositories. Use GitHub search syntax (language:kotlin, language:javascript). Call again for a new language or follow-up like 'what about go?'."""
        return wrap_github_tool(g.search_my_repos, "search_my_repos")(
            query=query, max_results=max_results
        )

    @tool
    def list_branches(owner: str = "", repo: str = "", max_results: int = 20) -> str:
        """List branches in a repository."""
        return wrap_github_tool(g.list_branches, "list_branches")(
            owner=owner or _owner_default(),
            repo=repo or _repo_default(),
            max_results=max_results,
        )

    @tool
    def list_releases(owner: str = "", repo: str = "", max_results: int = 10) -> str:
        """List published releases for a repository."""
        return wrap_github_tool(g.list_releases, "list_releases")(
            owner=owner or _owner_default(),
            repo=repo or _repo_default(),
            max_results=max_results,
        )

    @tool
    def get_me() -> str:
        """Get the signed-in GitHub user's profile."""
        return wrap_github_tool(g.get_me, "get_me")()

    return [
        list_my_repos,
        get_repo,
        search_my_repos,
        list_branches,
        list_releases,
        get_me,
    ]

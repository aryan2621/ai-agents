from langchain_core.tools import BaseTool, tool

from app.services.github_clients import GitHubClients
from app.tools._errors import wrap_github_tool


def build_code_tools(
    github: GitHubClients, workspace_context: dict[str, str] | None = None
) -> list[BaseTool]:
    g = github
    ctx = workspace_context or {}

    def _owner_default() -> str:
        return ctx.get("owner") or ""

    def _repo_default() -> str:
        return ctx.get("repo") or ""

    @tool
    def get_file_contents(
        path: str,
        owner: str = "",
        repo: str = "",
        ref: str = "",
    ) -> str:
        """Read a file (or list a directory) in a repository. ref is an optional branch or SHA."""
        return wrap_github_tool(g.get_file_contents, "get_file_contents")(
            path=path,
            owner=owner or _owner_default(),
            repo=repo or _repo_default(),
            ref=ref,
        )

    @tool
    def search_code(
        query: str,
        owner: str = "",
        repo: str = "",
        max_results: int = 10,
    ) -> str:
        """Search code. Scoped to the active repo when owner/repo are known."""
        return wrap_github_tool(g.search_code, "search_code")(
            query=query,
            owner=owner or _owner_default(),
            repo=repo or _repo_default(),
            max_results=max_results,
        )

    @tool
    def list_commits(
        owner: str = "",
        repo: str = "",
        sha: str = "",
        max_results: int = 10,
    ) -> str:
        """List recent commits. sha can be a branch name."""
        return wrap_github_tool(g.list_commits, "list_commits")(
            owner=owner or _owner_default(),
            repo=repo or _repo_default(),
            sha=sha,
            max_results=max_results,
        )

    return [get_file_contents, search_code, list_commits]

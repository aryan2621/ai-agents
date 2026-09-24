from langchain_core.tools import BaseTool, tool

from app.services.github_clients import GitHubClients
from app.tools._errors import wrap_github_tool


def build_issues_tools(
    github: GitHubClients, workspace_context: dict[str, str] | None = None
) -> list[BaseTool]:
    g = github
    ctx = workspace_context or {}

    def _owner_default() -> str:
        return ctx.get("owner") or ""

    def _repo_default() -> str:
        return ctx.get("repo") or ""

    @tool
    def list_issues(
        owner: str = "",
        repo: str = "",
        state: str = "open",
        max_results: int = 10,
    ) -> str:
        """List issues in a repository. state is open, closed, or all."""
        return wrap_github_tool(g.list_issues, "list_issues")(
            owner=owner or _owner_default(),
            repo=repo or _repo_default(),
            state=state,
            max_results=max_results,
        )

    @tool
    def get_issue(owner: str = "", repo: str = "", issue_number: int = 0) -> str:
        """Get one issue by number. Uses the active issue in this chat when omitted."""
        return wrap_github_tool(g.get_issue, "get_issue")(
            owner=owner or _owner_default(),
            repo=repo or _repo_default(),
            issue_number=issue_number,
        )

    @tool
    def create_issue(title: str, body: str = "", owner: str = "", repo: str = "") -> str:
        """Create an issue in a repository."""
        return wrap_github_tool(g.create_issue, "create_issue")(
            title=title,
            body=body,
            owner=owner or _owner_default(),
            repo=repo or _repo_default(),
        )

    @tool
    def add_issue_comment(
        body: str,
        owner: str = "",
        repo: str = "",
        issue_number: int = 0,
    ) -> str:
        """Comment on an issue."""
        return wrap_github_tool(g.add_issue_comment, "add_issue_comment")(
            body=body,
            owner=owner or _owner_default(),
            repo=repo or _repo_default(),
            issue_number=issue_number,
        )

    @tool
    def update_issue(
        owner: str = "",
        repo: str = "",
        issue_number: int = 0,
        state: str = "",
        title: str = "",
        body: str = "",
    ) -> str:
        """Update an issue title, body, or state (open/closed)."""
        return wrap_github_tool(g.update_issue, "update_issue")(
            owner=owner or _owner_default(),
            repo=repo or _repo_default(),
            issue_number=issue_number,
            state=state,
            title=title,
            body=body,
        )

    @tool
    def list_issue_comments(
        owner: str = "",
        repo: str = "",
        issue_number: int = 0,
        max_results: int = 20,
    ) -> str:
        """List comments on an issue or pull request."""
        return wrap_github_tool(g.list_issue_comments, "list_issue_comments")(
            owner=owner or _owner_default(),
            repo=repo or _repo_default(),
            issue_number=issue_number,
            max_results=max_results,
        )

    @tool
    def search_issues(query: str, max_results: int = 10) -> str:
        """Search issues across GitHub. Use GitHub search syntax, e.g. is:issue assignee:@me."""
        return wrap_github_tool(g.search_issues, "search_issues")(
            query=query, max_results=max_results
        )

    return [
        list_issues,
        get_issue,
        create_issue,
        add_issue_comment,
        update_issue,
        list_issue_comments,
        search_issues,
    ]

from langchain_core.tools import BaseTool, tool

from app.services.github_clients import GitHubClients
from app.tools._errors import wrap_github_tool


def build_pulls_tools(
    github: GitHubClients, workspace_context: dict[str, str] | None = None
) -> list[BaseTool]:
    g = github
    ctx = workspace_context or {}

    def _owner_default() -> str:
        return ctx.get("owner") or ""

    def _repo_default() -> str:
        return ctx.get("repo") or ""

    @tool
    def list_pull_requests(
        owner: str = "",
        repo: str = "",
        state: str = "open",
        max_results: int = 10,
    ) -> str:
        """List pull requests in a repository. state is open, closed, or all."""
        return wrap_github_tool(g.list_pull_requests, "list_pull_requests")(
            owner=owner or _owner_default(),
            repo=repo or _repo_default(),
            state=state,
            max_results=max_results,
        )

    @tool
    def get_pull_request(owner: str = "", repo: str = "", pr_number: int = 0) -> str:
        """Get one pull request by number. Uses the active PR in this chat when omitted."""
        return wrap_github_tool(g.get_pull_request, "get_pull_request")(
            owner=owner or _owner_default(),
            repo=repo or _repo_default(),
            pr_number=pr_number,
        )

    @tool
    def create_pull_request(
        title: str,
        head: str,
        base: str,
        body: str = "",
        owner: str = "",
        repo: str = "",
    ) -> str:
        """Create a pull request. head and base are branch names."""
        return wrap_github_tool(g.create_pull_request, "create_pull_request")(
            title=title,
            head=head,
            base=base,
            body=body,
            owner=owner or _owner_default(),
            repo=repo or _repo_default(),
        )

    @tool
    def add_pr_comment(
        body: str,
        owner: str = "",
        repo: str = "",
        pr_number: int = 0,
    ) -> str:
        """Comment on a pull request."""
        return wrap_github_tool(g.add_pr_comment, "add_pr_comment")(
            body=body,
            owner=owner or _owner_default(),
            repo=repo or _repo_default(),
            pr_number=pr_number,
        )

    @tool
    def list_pr_files(
        owner: str = "",
        repo: str = "",
        pr_number: int = 0,
        max_results: int = 20,
    ) -> str:
        """List files changed in a pull request."""
        return wrap_github_tool(g.list_pr_files, "list_pr_files")(
            owner=owner or _owner_default(),
            repo=repo or _repo_default(),
            pr_number=pr_number,
            max_results=max_results,
        )

    @tool
    def merge_pull_request(
        owner: str = "",
        repo: str = "",
        pr_number: int = 0,
        merge_method: str = "merge",
    ) -> str:
        """Merge a pull request. merge_method is merge, squash, or rebase."""
        return wrap_github_tool(g.merge_pull_request, "merge_pull_request")(
            owner=owner or _owner_default(),
            repo=repo or _repo_default(),
            pr_number=pr_number,
            merge_method=merge_method,
        )

    @tool
    def search_issues(query: str, max_results: int = 10) -> str:
        """Search pull requests across GitHub. Use GitHub search syntax, e.g. is:pr is:open author:@me."""
        return wrap_github_tool(g.search_issues, "search_issues")(
            query=query, max_results=max_results
        )

    return [
        list_pull_requests,
        get_pull_request,
        create_pull_request,
        add_pr_comment,
        list_pr_files,
        merge_pull_request,
        search_issues,
    ]

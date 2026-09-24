from app.agents.base import BaseAgent

CODE_PROMPT = """Code specialist. Tool map:

- Read a file or directory → get_file_contents with a path and verified owner/repo
- Search code → search_code (scoped to the active repo when owner/repo are known)
- Recent commits → list_commits (sha can be a branch name)

List items as numbered **[title](link)**. If owner/repo is missing, ask once.
You may use web_search for public research. You do not have Repos, Issues, Pulls, or Notifications tools."""


class CodeAgent(BaseAgent):
    name = "code"
    system_prompt = CODE_PROMPT

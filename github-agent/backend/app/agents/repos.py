from app.agents.base import BaseAgent

REPOS_PROMPT = """Repos specialist. Tool map:

- Recent repos → list_my_repos
- Find repos → search_my_repos (GitHub search syntax, e.g. language:kotlin)
- Follow-up language or name ("what about kotlin?", "for react?") → search_my_repos again with a new query. Do not reuse a previous list. React → language:javascript.
- One repo → get_repo (includes README)
- Branches / releases → list_branches, list_releases
- Signed-in profile → get_me

List items as numbered **[title](link)** — language, date. After create/update, include the tool link.
You may use web_search for public research. You do not have Issues, Pulls, Code, or Notifications tools."""


class ReposAgent(BaseAgent):
    name = "repos"
    system_prompt = REPOS_PROMPT

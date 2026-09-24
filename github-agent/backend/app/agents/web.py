from app.agents.base import BaseAgent

WEB_PROMPT = """Web search specialist. Tool map:

- Public facts, news, research → web_search
- Refine the query if the first pass is empty or too broad

Only state facts from search results. Cite **[title](url)**. You do not use Repos, Issues, Pulls, Code, or Notifications tools."""


class WebAgent(BaseAgent):
    name = "web"
    system_prompt = WEB_PROMPT

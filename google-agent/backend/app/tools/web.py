from langchain_core.tools import BaseTool, tool

from app.services.platform.tavily_search import TavilySearchClient


def build_web_tools(tavily: TavilySearchClient) -> list[BaseTool]:
    client = tavily

    @tool
    def web_search(query: str, count: int = 5) -> str:
        """Search the public web via Tavily. Returns JSON with titles, URLs, and snippets."""
        return client.web_search(query=query, count=count)

    return [web_search]

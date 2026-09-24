from __future__ import annotations

import logging
import os

import httpx

from app.utils.tools import tool_error, tool_result

logger = logging.getLogger("app.tavily_search")

TAVILY_SEARCH_URL = "https://api.tavily.com/search"
DEFAULT_RESULT_COUNT = 5
MAX_RESULT_COUNT = 10


class TavilySearchClient:
    def __init__(self, api_key: str) -> None:
        self._api_key = api_key.strip()

    @property
    def configured(self) -> bool:
        return bool(self._api_key)

    def web_search(self, query: str, count: int = DEFAULT_RESULT_COUNT) -> str:
        if not self.configured:
            return tool_error(
                "Tavily API key is not configured.",
                next_step=(
                    "Add your API key in Settings → Web Search "
                    "(get one at https://tavily.com)."
                ),
            )

        query = query.strip()
        if not query:
            return tool_error("Search query cannot be empty.")

        count = max(1, min(int(count), MAX_RESULT_COUNT))

        try:
            with httpx.Client(timeout=20.0) as client:
                response = client.post(
                    TAVILY_SEARCH_URL,
                    json={
                        "api_key": self._api_key,
                        "query": query,
                        "max_results": count,
                        "search_depth": "basic",
                    },
                )
        except httpx.TimeoutException:
            return tool_error(
                "Tavily search request timed out.",
                next_step="Retry the search.",
            )
        except httpx.HTTPError as exc:
            logger.warning("Tavily HTTP error: %s", exc)
            return tool_error(f"Tavily search request failed: {exc}")

        if response.status_code == 401:
            return tool_error(
                "Tavily API key is invalid or unauthorized.",
                next_step="Check your API key in Settings → Web Search.",
            )
        if response.status_code == 429:
            return tool_error(
                "Tavily rate limit reached.",
                next_step="Wait a moment and retry.",
            )
        if response.status_code >= 400:
            return tool_error(
                f"Tavily search error ({response.status_code}).",
                next_step="Retry or check your Tavily API subscription.",
            )

        try:
            data = response.json()
        except ValueError:
            return tool_error("Tavily search returned an invalid response.")

        raw_results = data.get("results") or []
        results: list[dict[str, str]] = []
        for item in raw_results[:count]:
            title = (item.get("title") or "").strip()
            url = (item.get("url") or "").strip()
            snippet = (item.get("content") or item.get("snippet") or "").strip()
            if title and url:
                results.append({"title": title, "url": url, "snippet": snippet})

        if not results:
            return tool_result(
                "ok",
                f'No web results found for "{query}".',
                query=query,
                result_count=0,
                results=[],
            )

        bullets: list[str] = []
        for result in results:
            line = f"- **[{result['title']}]({result['url']})**"
            if result["snippet"]:
                line += f" — {result['snippet']}"
            bullets.append(line)

        summary = f'Found {len(results)} result(s) for "{query}":\n' + "\n".join(bullets)
        return tool_result(
            "ok",
            summary,
            next_step="Cite these sources in your reply using the same markdown links.",
            query=query,
            result_count=len(results),
            results=results,
        )


def _tavily_key_from_process_env() -> str:
    return (
        os.environ.get("TAVILY_API_KEY")
        or os.environ.get("TAVILY_SEARCH_API_KEY")
        or ""
    ).strip()


def resolve_tavily_api_key(user_settings_key: str | None = None) -> str:
    from app.config import get_settings, read_tavily_api_key_from_env_files

    user_key = (user_settings_key or "").strip()
    if user_key:
        return user_key

    for source in (
        lambda: get_settings().tavily_search_api_key.strip(),
        _tavily_key_from_process_env,
        read_tavily_api_key_from_env_files,
    ):
        key = source()
        if key:
            return key
    return ""

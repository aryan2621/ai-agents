import json
import logging
from typing import Any

from langchain_core.tools import BaseTool, tool

from app.services.google_clients import GoogleClients
from app.tools._errors import wrap_google_tool

logger = logging.getLogger("app.tools.docs")


def build_docs_tools(
    google: GoogleClients, workspace_context: dict[str, str] | None = None
) -> list[BaseTool]:
    g = google
    ctx = workspace_context if workspace_context is not None else {}

    @tool
    def list_documents(max_results: int = 20) -> str:
        """List the user's Google Docs (name and id). Use when no document ID is known."""
        return wrap_google_tool(g.list_documents, "list_documents")(max_results=max_results)

    @tool
    def search_documents(query: str, max_results: int = 10) -> str:
        """Search Google Docs by name."""
        return wrap_google_tool(g.search_documents, "search_documents")(
            query=query, max_results=max_results
        )

    @tool
    def create_document(title: str) -> str:
        """Create a new Google Doc. Returns JSON with id and document_id — use that id for follow-up tools."""
        return wrap_google_tool(g.create_document, "create_document")(title=title)

    @tool
    def get_document_text(document_id: str) -> str:
        """Read text content of a Google Doc by ID from list/search results."""
        return wrap_google_tool(g.get_document_text, "get_document_text")(
            document_id=document_id
        )

    @tool
    def append_to_document(document_id: str, text: str) -> str:
        """Append text to a Google Doc. document_id must come from create_document or list_documents."""
        known_id = ctx.get("document_id", "")
        result = wrap_google_tool(g.append_to_document, "append_to_document")(
            document_id=document_id, text=text
        )
        try:
            data = json.loads(result)
        except json.JSONDecodeError:
            return result
        if (
            data.get("status") == "error"
            and known_id
            and document_id.strip() != known_id
        ):
            logger.info("append_to_document retry with known document_id=%s", known_id)
            result = wrap_google_tool(g.append_to_document, "append_to_document")(
                document_id=known_id, text=text
            )
        return result

    return [
        list_documents,
        search_documents,
        create_document,
        get_document_text,
        append_to_document,
    ]

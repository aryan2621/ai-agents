from langchain_core.tools import BaseTool, tool

from app.services.google_clients import GoogleClients
from app.tools._errors import wrap_google_tool


def build_drive_tools(
    google: GoogleClients, workspace_context: dict[str, str] | None = None
) -> list[BaseTool]:
    g = google

    @tool
    def list_my_files(max_results: int = 20) -> str:
        """List the user's recent Drive files (id and name)."""
        return wrap_google_tool(g.list_my_files, "list_my_files")(max_results=max_results)

    @tool
    def list_folder(folder_id: str = "root", max_results: int = 20) -> str:
        """List files inside a Drive folder (folder_id 'root' for top level)."""
        return wrap_google_tool(g.list_folder, "list_folder")(
            folder_id=folder_id, max_results=max_results
        )

    @tool
    def search_files(query: str, max_results: int = 10) -> str:
        """Search Google Drive files by filename keyword (e.g. 'budget')."""
        return wrap_google_tool(g.search_files, "search_files")(
            query=query, max_results=max_results
        )

    @tool
    def list_recent_shared(max_results: int = 10) -> str:
        """List files recently shared with the user."""
        return wrap_google_tool(g.list_recent_shared, "list_recent_shared")(
            max_results=max_results
        )

    @tool
    def get_file_metadata(file_id: str) -> str:
        """Get metadata for a file by ID from list/search results."""
        return wrap_google_tool(g.get_file_metadata, "get_file_metadata")(file_id=file_id)

    @tool
    def create_folder(name: str, parent_id: str = "") -> str:
        """Create a Drive folder. Returns JSON with id and folder_id."""
        return wrap_google_tool(g.create_folder, "create_folder")(
            name=name, parent_id=parent_id
        )

    @tool
    def share_file(file_id: str, email: str, role: str = "reader") -> str:
        """Share a file with a user by email (role: reader, writer, or commenter)."""
        return wrap_google_tool(g.share_file, "share_file")(
            file_id=file_id, email=email, role=role
        )

    @tool
    def trash_file(file_id: str) -> str:
        """Move a file to trash."""
        return wrap_google_tool(g.trash_file, "trash_file")(file_id=file_id)

    return [
        list_my_files,
        list_folder,
        search_files,
        list_recent_shared,
        get_file_metadata,
        create_folder,
        share_file,
        trash_file,
    ]

from __future__ import annotations

from app.services.google.support import (
    _build_drive_name_search_query,
    _created_response,
    _file_item,
    _invalid_id_response,
    _list_text,
    _tool_error,
    _tool_result,
    _linked_action_summary,
)


class DriveMixin:
    def search_files(self, query: str, max_results: int = 10) -> str:
        drive_query = _build_drive_name_search_query(query)
        result = (
            self._drive.files()
            .list(q=drive_query, pageSize=max_results, fields="files(id,name,mimeType,modifiedTime,webViewLink)")
            .execute()
        )
        files = [_file_item(f) for f in result.get("files", [])]
        count = len(files)
        return _tool_result(
            "ok",
            f"Found {count} file(s) matching '{query}'." if count else f"No files matched '{query}'.",
            next_step="If the user refers to a file, call the follow-up tool yourself with files[].file_id. Never ask the user for an id.",
            query=query,
            count=count,
            preview=_list_text(files),
            files=files,
        )

    def list_recent_shared(self, max_results: int = 10) -> str:
        result = (
            self._drive.files()
            .list(
                q="sharedWithMe = true",
                pageSize=max_results,
                orderBy="sharedWithMeTime desc",
                fields="files(id,name,mimeType,modifiedTime,webViewLink)",
            )
            .execute()
        )
        files = [_file_item(f) for f in result.get("files", [])]
        count = len(files)
        return _tool_result(
            "ok",
            f"Found {count} recently shared file(s)." if count else "No recently shared files.",
            next_step="If the user refers to a file, call the follow-up tool yourself with files[].file_id. Never ask the user for an id.",
            count=count,
            preview=_list_text(files),
            files=files,
        )

    def get_file_metadata(self, file_id: str) -> str:
        invalid = _invalid_id_response(file_id, "file_id")
        if invalid:
            return invalid
        file = (
            self._drive.files()
            .get(fileId=file_id, fields="id,name,mimeType,size,modifiedTime,webViewLink,owners")
            .execute()
        )
        item = _file_item(file)
        item["mimeType"] = file.get("mimeType", "")
        item["modifiedTime"] = file.get("modifiedTime", "")
        file_name = item.get("name", "")
        file_link = item.get("webViewLink", "")
        return _tool_result(
            "ok",
            _linked_action_summary(
                "Retrieved file",
                file_name,
                file_link,
                fallback=f'Retrieved metadata for "{file_name}".',
            ),
            next_step="If the user wants to share or trash this file, call the tool yourself with this file_id. Never ask the user for an id.",
            **item,
            file_id=item.get("id"),
            webViewLink=file_link,
        )

    def list_my_files(self, max_results: int = 20) -> str:
        result = (
            self._drive.files()
            .list(
                q="'me' in owners and trashed=false",
                pageSize=max_results,
                orderBy="modifiedTime desc",
                fields="files(id,name,mimeType,modifiedTime,webViewLink,parents)",
            )
            .execute()
        )
        files = [_file_item(f) for f in result.get("files", [])]
        count = len(files)
        return _tool_result(
            "ok",
            f"Found {count} recent file(s)." if count else "No recent files found.",
            next_step="If the user refers to a file, call the follow-up tool yourself with files[].file_id. Never ask the user for an id.",
            count=count,
            preview=_list_text(files),
            files=files,
        )

    def list_folder(self, folder_id: str = "root", max_results: int = 20) -> str:
        parent = folder_id.strip() or "root"
        result = (
            self._drive.files()
            .list(
                q=f"'{parent}' in parents and trashed=false",
                pageSize=max_results,
                orderBy="folder,name",
                fields="files(id,name,mimeType,modifiedTime,webViewLink)",
            )
            .execute()
        )
        files = [_file_item(f) for f in result.get("files", [])]
        count = len(files)
        return _tool_result(
            "ok",
            f"Found {count} file(s) in folder {parent}." if count else f"Folder {parent} is empty.",
            next_step="If the user refers to a file, call the follow-up tool yourself with files[].file_id. Never ask the user for an id.",
            folder_id=parent,
            count=count,
            preview=_list_text(files),
            files=files,
        )

    def create_folder(self, name: str, parent_id: str = "") -> str:
        metadata: dict = {
            "name": name,
            "mimeType": "application/vnd.google-apps.folder",
        }
        if parent_id.strip():
            metadata["parents"] = [parent_id.strip()]
        folder = (
            self._drive.files()
            .create(body=metadata, fields="id,name,webViewLink")
            .execute()
        )
        item = _file_item(folder)
        return _created_response(
            folder.get("id", ""),
            id_key="folder_id",
            name=item.get("name", name),
            webViewLink=item.get("webViewLink", ""),
            folder=item,
        )

    def share_file(self, file_id: str, email: str, role: str = "reader") -> str:
        if role not in ("reader", "writer", "commenter"):
            return _tool_error("role must be reader, writer, or commenter.")
        perm = (
            self._drive.permissions()
            .create(
                fileId=file_id,
                body={"type": "user", "role": role, "emailAddress": email},
                sendNotificationEmail=True,
                fields="id,role,emailAddress",
            )
            .execute()
        )
        return _tool_result(
            "shared",
            f"Shared file {file_id} with {email} as {role}.",
            file_id=file_id,
            permission=perm,
        )

    def trash_file(self, file_id: str) -> str:
        invalid = _invalid_id_response(file_id, "file_id")
        if invalid:
            return invalid
        self._drive.files().update(fileId=file_id, body={"trashed": True}).execute()
        return _tool_result("trashed", f"Moved file {file_id} to trash.", file_id=file_id)

    # --- Docs ---

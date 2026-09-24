from __future__ import annotations

from app.services.google.support import (
    DOCS_MIME,
    _build_drive_name_search_query,
    _created_response,
    _document_url,
    _file_item,
    _invalid_id_response,
    _list_text,
    _tool_result,
    _linked_action_summary,
)


class DocsMixin:
    def list_documents(self, max_results: int = 20) -> str:
        result = (
            self._drive.files()
            .list(
                q=f"mimeType='{DOCS_MIME}' and trashed=false",
                pageSize=max_results,
                orderBy="modifiedTime desc",
                fields="files(id,name,modifiedTime,webViewLink)",
            )
            .execute()
        )
        files = result.get("files", [])
        items = [_file_item(f, id_alias="document_id") for f in files]
        count = len(items)
        return _tool_result(
            "ok",
            f"Found {count} Google Doc(s)." if count else "No Google Docs found.",
            next_step="If the user refers to a document, call get_document_text yourself with documents[].document_id. Never ask the user for an id.",
            count=count,
            preview=_list_text(items),
            documents=items,
        )

    def search_documents(self, query: str, max_results: int = 10) -> str:
        drive_query = _build_drive_name_search_query(query, mime_type=DOCS_MIME)
        result = (
            self._drive.files()
            .list(
                q=drive_query,
                pageSize=max_results,
                orderBy="modifiedTime desc",
                fields="files(id,name,modifiedTime,webViewLink)",
            )
            .execute()
        )
        files = [_file_item(f, id_alias="document_id") for f in result.get("files", [])]
        count = len(files)
        return _tool_result(
            "ok",
            f"Found {count} document(s) matching '{query}'." if count else f"No documents matched '{query}'.",
            next_step="If the user refers to a document, call get_document_text yourself with documents[].document_id. Never ask the user for an id.",
            query=query,
            count=count,
            preview=_list_text(files),
            documents=files,
        )

    def create_document(self, title: str) -> str:
        created = (
            self._drive.files()
            .create(
                body={"name": title, "mimeType": DOCS_MIME},
                fields="id,name,webViewLink",
            )
            .execute()
        )
        return _created_response(
            created.get("id", ""),
            id_key="document_id",
            name=created.get("name"),
            webViewLink=created.get("webViewLink")
            or _document_url(created.get("id", "")),
        )

    def get_document_text(self, document_id: str) -> str:
        invalid = _invalid_id_response(document_id, "document_id")
        if invalid:
            return invalid
        doc = self._docs.documents().get(documentId=document_id).execute()
        content = []
        for element in doc.get("body", {}).get("content", []):
            para = element.get("paragraph")
            if not para:
                continue
            text = ""
            for elem in para.get("elements", []):
                text += elem.get("textRun", {}).get("content", "")
            if text.strip():
                content.append(text.strip())
        content_text = "\n".join(content[:50])
        title = doc.get("title") or "(untitled)"
        doc_link = _document_url(document_id)
        return _tool_result(
            "ok",
            _linked_action_summary(
                "Read document",
                title,
                doc_link,
                fallback=f'Read document "{title}" ({len(content)} paragraph(s)).',
            ),
            next_step="If the user wants to append, call append_to_document yourself with this document_id. Never ask the user for an id.",
            document_id=document_id,
            title=title,
            webViewLink=doc_link,
            paragraph_count=len(content),
            content=content_text,
        )

    def append_to_document(self, document_id: str, text: str) -> str:
        invalid = _invalid_id_response(document_id, "document_id")
        if invalid:
            return invalid
        doc = self._docs.documents().get(documentId=document_id).execute()
        end_index = doc.get("body", {}).get("content", [{}])[-1].get("endIndex", 1) - 1
        requests = [{"insertText": {"location": {"index": end_index}, "text": text}}]
        self._docs.documents().batchUpdate(
            documentId=document_id, body={"requests": requests}
        ).execute()
        return _tool_result(
            "appended",
            f"Appended {len(text)} character(s) to document {document_id}.",
            document_id=document_id,
            characters_added=len(text),
        )

    # --- Sheets ---

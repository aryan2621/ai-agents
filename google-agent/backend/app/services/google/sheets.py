from __future__ import annotations

from googleapiclient.errors import HttpError

from app.services.google.support import (
    SHEET_PAGE_DEFAULT,
    SHEET_PAGE_MAX,
    SHEETS_MIME,
    _build_drive_name_search_query,
    _created_response,
    _file_item,
    _google_http_error_message,
    _invalid_id_response,
    _list_text,
    _normalize_range_a1,
    _pad_values,
    _spreadsheet_url,
    _table_preview,
    _tool_error,
    _tool_result,
    _linked_action_summary,
)
import logging

logger = logging.getLogger("app.google")


class SheetsMixin:
    def list_spreadsheets(self, max_results: int = 20) -> str:
        result = (
            self._drive.files()
            .list(
                q=f"mimeType='{SHEETS_MIME}' and trashed=false",
                pageSize=max_results,
                orderBy="modifiedTime desc",
                fields="files(id,name,mimeType,modifiedTime,webViewLink)",
            )
            .execute()
        )
        raw_files = result.get("files", [])
        items = [_file_item(f, id_alias="spreadsheet_id") for f in raw_files]
        list_text = _list_text(items)
        count = len(items)
        return _tool_result(
            "ok",
            f"Found {count} spreadsheet(s)." if count else "No spreadsheets found.",
            next_step="If the user refers to a spreadsheet, call read_range yourself with spreadsheets[].spreadsheet_id. Never ask the user for an id.",
            count=count,
            preview=list_text,
            list_text=list_text,
            spreadsheets=items,
        )

    def search_spreadsheets(self, query: str, max_results: int = 10) -> str:
        drive_query = _build_drive_name_search_query(query, mime_type=SHEETS_MIME)
        result = (
            self._drive.files()
            .list(
                q=drive_query,
                pageSize=max_results,
                orderBy="modifiedTime desc",
                fields="files(id,name,mimeType,modifiedTime,webViewLink)",
            )
            .execute()
        )
        raw_files = result.get("files", [])
        items = [_file_item(f, id_alias="spreadsheet_id") for f in raw_files]
        list_text = _list_text(items)
        count = len(items)
        return _tool_result(
            "ok",
            f"Found {count} spreadsheet(s) matching '{query}'." if count else f"No spreadsheets matched '{query}'.",
            next_step="If the user refers to a spreadsheet, call read_range yourself with spreadsheets[].spreadsheet_id. Never ask the user for an id.",
            query=query,
            count=count,
            preview=list_text,
            list_text=list_text,
            spreadsheets=items,
        )

    def trash_spreadsheet(self, spreadsheet_id: str) -> str:
        invalid = _invalid_id_response(spreadsheet_id)
        if invalid:
            logger.warning("Google API trash_spreadsheet rejected id=%r", spreadsheet_id)
            return invalid
        try:
            self._drive.files().update(fileId=spreadsheet_id, body={"trashed": True}).execute()
        except HttpError as exc:
            return _tool_error(
                _google_http_error_message(exc, "spreadsheet_id"),
                spreadsheet_id=spreadsheet_id,
            )
        return _tool_result(
            "trashed",
            f"Moved spreadsheet {spreadsheet_id} to trash.",
            spreadsheet_id=spreadsheet_id,
        )

    def trash_all_spreadsheets(self, max_results: int = 100) -> str:
        result = (
            self._drive.files()
            .list(
                q=f"mimeType='{SHEETS_MIME}' and trashed=false",
                pageSize=max_results,
                fields="files(id,name)",
            )
            .execute()
        )
        trashed_names: list[str] = []
        for file in result.get("files", []):
            self._drive.files().update(fileId=file["id"], body={"trashed": True}).execute()
            trashed_names.append(file.get("name", ""))
        count = len(trashed_names)
        return _tool_result(
            "trashed" if trashed_names else "none_found",
            f"Moved {count} spreadsheet(s) to trash." if trashed_names else "No spreadsheets to trash.",
            count=count,
            trashed_names=trashed_names,
        )

    def trash_spreadsheets_by_names(self, names: list[str]) -> str:
        requested = {name.strip().lower() for name in names if name.strip()}
        if not requested:
            return _tool_error("No spreadsheet names provided.")

        result = (
            self._drive.files()
            .list(
                q=f"mimeType='{SHEETS_MIME}' and trashed=false",
                pageSize=100,
                fields="files(id,name)",
            )
            .execute()
        )
        trashed_names: list[str] = []
        remaining = set(requested)
        for file in result.get("files", []):
            file_name = file.get("name", "")
            key = file_name.lower()
            if key not in remaining:
                continue
            self._drive.files().update(fileId=file["id"], body={"trashed": True}).execute()
            trashed_names.append(file_name)
            remaining.discard(key)

        count = len(trashed_names)
        summary = (
            f"Trashed {count} spreadsheet(s): {', '.join(trashed_names)}."
            if trashed_names
            else "No matching spreadsheets were trashed."
        )
        return _tool_result(
            "trashed" if trashed_names else "none_trashed",
            summary,
            count=count,
            trashed_names=trashed_names,
            not_found=sorted(remaining),
        )

    def create_spreadsheet(self, title: str) -> str:
        created = self._sheets.spreadsheets().create(
            body={"properties": {"title": title}}
        ).execute()
        spreadsheet_id = created.get("spreadsheetId", "")
        sheet_url = _spreadsheet_url(spreadsheet_id)
        return _created_response(
            spreadsheet_id,
            id_key="spreadsheet_id",
            title=created.get("properties", {}).get("title", title),
            webViewLink=sheet_url,
            spreadsheetUrl=sheet_url,
        )

    def create_spreadsheet_with_data(
        self, title: str, values: list, range_a1: str = ""
    ) -> str:
        created = self._sheets.spreadsheets().create(
            body={"properties": {"title": title}}
        ).execute()
        spreadsheet_id = created.get("spreadsheetId", "")
        if not spreadsheet_id:
            return _tool_error("Create succeeded but no ID was returned from Google.")

        padded = _pad_values(values)
        num_cols = max((len(row) for row in padded), default=1)
        effective_range = range_a1.strip() or "Sheet1!A1"
        effective_range = _normalize_range_a1(effective_range, len(padded), num_cols)
        sheet_title = created.get("properties", {}).get("title", title)

        try:
            result = (
                self._sheets.spreadsheets()
                .values()
                .update(
                    spreadsheetId=spreadsheet_id,
                    range=effective_range,
                    valueInputOption="USER_ENTERED",
                    body={"values": padded},
                )
                .execute()
            )
        except HttpError as exc:
            return _tool_error(
                _google_http_error_message(exc, "spreadsheet_id"),
                spreadsheet_id=spreadsheet_id,
                title=sheet_title,
            )

        updated_cells = result.get("updatedCells", 0)
        sheet_url = _spreadsheet_url(spreadsheet_id)
        return _tool_result(
            "created",
            _linked_action_summary(
                f'Created spreadsheet and wrote {updated_cells} cell(s) to {effective_range}',
                sheet_title,
                sheet_url,
                fallback=(
                    f'Created spreadsheet "{sheet_title}" and wrote {updated_cells} cell(s) '
                    f"to {effective_range}."
                ),
            ),
            next_step=f"Call follow-up tools yourself with spreadsheet_id={spreadsheet_id}. Never ask the user for an id.",
            id=spreadsheet_id,
            spreadsheet_id=spreadsheet_id,
            title=sheet_title,
            webViewLink=sheet_url,
            spreadsheetUrl=sheet_url,
            range=effective_range,
            row_count=len(padded),
            column_count=num_cols,
            updatedCells=updated_cells,
            preview=_table_preview(padded),
            values=padded,
        )

    def get_spreadsheet_info(self, spreadsheet_id: str) -> str:
        invalid = _invalid_id_response(spreadsheet_id)
        if invalid:
            return invalid
        try:
            sheet = self._sheets.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
        except HttpError as exc:
            return _tool_error(
                _google_http_error_message(exc, "spreadsheet_id"),
                spreadsheet_id=spreadsheet_id,
            )
        sheets = [{"title": s["properties"]["title"], "sheetId": s["properties"]["sheetId"]}
                  for s in sheet.get("sheets", [])]
        title = sheet.get("properties", {}).get("title") or "(untitled)"
        tab_names = [s["title"] for s in sheets]
        sheet_url = _spreadsheet_url(spreadsheet_id)
        return _tool_result(
            "ok",
            _linked_action_summary(
                f'Spreadsheet has {len(sheets)} tab(s): {", ".join(tab_names) or "none"}',
                title,
                sheet_url,
                fallback=(
                    f'Spreadsheet "{title}" has {len(sheets)} tab(s): '
                    f'{", ".join(tab_names) or "none"}.'
                ),
            ),
            spreadsheet_id=spreadsheet_id,
            title=title,
            webViewLink=sheet_url,
            spreadsheetUrl=sheet_url,
            sheets=sheets,
        )

    def read_range(
        self,
        spreadsheet_id: str,
        range_a1: str,
        offset: int = 0,
        limit: int = SHEET_PAGE_DEFAULT,
    ) -> str:
        invalid = _invalid_id_response(spreadsheet_id)
        if invalid:
            return invalid
        try:
            result = (
                self._sheets.spreadsheets()
                .values()
                .get(spreadsheetId=spreadsheet_id, range=range_a1)
                .execute()
            )
            meta = (
                self._sheets.spreadsheets()
                .get(spreadsheetId=spreadsheet_id, fields="properties.title")
                .execute()
            )
        except HttpError as exc:
            return _tool_error(
                _google_http_error_message(exc, "spreadsheet_id"),
                spreadsheet_id=spreadsheet_id,
            )
        values = result.get("values", [])
        title = meta.get("properties", {}).get("title") or "(untitled)"
        row_count = len(values)
        col_count = max((len(row) for row in values), default=0)
        offset = max(0, int(offset))
        limit = max(1, min(int(limit), SHEET_PAGE_MAX))
        page = values[offset : offset + limit]
        has_more = offset + len(page) < row_count
        next_step = "Merge changes locally, then call write_range with the full updated table."
        if has_more:
            next_step = (
                f"If you need more rows, call again with offset={offset + limit} "
                "and the same limit. Never ask the user."
            )
        return _tool_result(
            "ok",
            (
                f'Read rows {offset}-{offset + len(page)} of {row_count} '
                f'({col_count} column(s)) from "{title}" ({range_a1}).'
                if row_count
                else f'No rows in "{title}" ({range_a1}).'
            ),
            next_step=next_step,
            spreadsheet_id=spreadsheet_id,
            title=title,
            range=range_a1,
            row_count=row_count,
            column_count=col_count,
            offset=offset,
            limit=limit,
            has_more=has_more,
            preview=_table_preview(page),
            values=page,
        )

    def write_range(self, spreadsheet_id: str, range_a1: str, values: list) -> str:
        invalid = _invalid_id_response(spreadsheet_id)
        if invalid:
            return invalid
        padded = _pad_values(values)
        num_cols = max((len(row) for row in padded), default=1)
        effective_range = _normalize_range_a1(range_a1, len(padded), num_cols)
        body = {"values": padded}
        try:
            result = (
                self._sheets.spreadsheets()
                .values()
                .update(
                    spreadsheetId=spreadsheet_id,
                    range=effective_range,
                    valueInputOption="USER_ENTERED",
                    body=body,
                )
                .execute()
            )
        except HttpError as exc:
            return _tool_error(
                _google_http_error_message(exc, "spreadsheet_id"),
                spreadsheet_id=spreadsheet_id,
                range=effective_range,
                next_step="Call read_range to inspect current data, fix values, then retry write_range.",
            )
        updated_cells = result.get("updatedCells", 0)
        return _tool_result(
            "updated",
            f"Wrote {updated_cells} cell(s) to {effective_range}.",
            next_step=f"Call follow-up tools yourself with spreadsheet_id={spreadsheet_id}. Never ask the user for an id.",
            spreadsheet_id=spreadsheet_id,
            range=effective_range,
            row_count=len(padded),
            column_count=num_cols,
            updatedCells=updated_cells,
            preview=_table_preview(padded),
            values=padded,
        )

    def append_range(self, spreadsheet_id: str, range_a1: str, values: list) -> str:
        invalid = _invalid_id_response(spreadsheet_id)
        if invalid:
            return invalid
        padded = _pad_values(values)
        if not padded:
            return _tool_error(
                "No rows to append.",
                spreadsheet_id=spreadsheet_id,
                next_step="Pass at least one row in values.",
            )
        num_cols = max((len(row) for row in padded), default=1)
        try:
            result = (
                self._sheets.spreadsheets()
                .values()
                .append(
                    spreadsheetId=spreadsheet_id,
                    range=range_a1,
                    valueInputOption="USER_ENTERED",
                    insertDataOption="INSERT_ROWS",
                    body={"values": padded},
                )
                .execute()
            )
        except HttpError as exc:
            return _tool_error(
                _google_http_error_message(exc, "spreadsheet_id"),
                spreadsheet_id=spreadsheet_id,
                range=range_a1,
                next_step="Call read_range to inspect headers, then retry append_range.",
            )
        updates = result.get("updates", {})
        updated_cells = updates.get("updatedCells", 0)
        updated_range = updates.get("updatedRange", range_a1)
        return _tool_result(
            "appended",
            f"Appended {len(padded)} row(s) ({updated_cells} cell(s)) to {updated_range}.",
            next_step=f"Call follow-up tools yourself with spreadsheet_id={spreadsheet_id}. Never ask the user for an id.",
            spreadsheet_id=spreadsheet_id,
            range=updated_range,
            row_count=len(padded),
            column_count=num_cols,
            updatedCells=updated_cells,
            preview=_table_preview(padded),
            values=padded,
        )

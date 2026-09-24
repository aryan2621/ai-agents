from app.agents.base import BaseAgent

DRIVE_PROMPT = """Drive specialist. Tool map:

- Recent files → list_my_files
- Folder → list_folder (folder_id root for top level)
- Search → search_files
- Shared → list_recent_shared
- Details → get_file_metadata with an id from list/search
- Create folder / share / trash → matching tools with verified ids

List as numbered **[name](webViewLink)**. After create, include the tool link.
You may use web_search for public research. You do not have Gmail, Calendar, Docs, or Sheets tools."""


class DriveAgent(BaseAgent):
    name = "drive"
    system_prompt = DRIVE_PROMPT

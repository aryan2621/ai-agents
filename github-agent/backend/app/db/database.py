"""Local file storage, in the style of the other desktop apps (Jarvis, Relay): JSON files in the
app's data folder, written atomically. No database server, no ORM.

    <data dir>/account.json              signed-in user and session
    <data dir>/settings.json             per-user settings
    <data dir>/conversations/<id>.json   one file per chat, messages included

Routes and services receive the shared Store through `get_db`: they read and change the records in memory, then `await session.commit()` saves every
file whose contents changed.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
from collections.abc import AsyncGenerator
from dataclasses import asdict, fields
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.config import _app_data_dir
from app.db.models import Conversation, Message, OAuthToken, User, UserSettings

logger = logging.getLogger(__name__)


def _dump(value: Any) -> Any:
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, dict):
        return {k: _dump(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_dump(v) for v in value]
    return value


def _when(value: Any) -> datetime:
    if isinstance(value, datetime):
        moment = value
    else:
        try:
            moment = datetime.fromisoformat(str(value))
        except ValueError:
            moment = datetime.now(timezone.utc)
    return moment if moment.tzinfo else moment.replace(tzinfo=timezone.utc)


def _build(cls: type, data: dict) -> Any:
    """A record from saved JSON, ignoring keys an older or newer version wrote."""
    names = {f.name for f in fields(cls)}
    values = {k: v for k, v in data.items() if k in names}
    for key in ("created_at", "updated_at", "timestamp"):
        if key in values:
            values[key] = _when(values[key])
    return cls(**values)


def _write_atomic(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    pending = path.with_name(f".{path.name}.tmp")
    with open(pending, "w", encoding="utf-8") as handle:
        handle.write(text)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(pending, path)


class Store:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.users: dict[str, User] = {}
        self.tokens: dict[str, OAuthToken] = {}  # by user id
        self.settings: dict[str, UserSettings] = {}  # by user id
        self.conversations: dict[str, Conversation] = {}
        self._saved: dict[Path, str] = {}  # last text written per file
        self._lock = asyncio.Lock()

    # Paths -------------------------------------------------------------------------------
    @property
    def _account_path(self) -> Path:
        return self.root / "account.json"

    @property
    def _settings_path(self) -> Path:
        return self.root / "settings.json"

    @property
    def _conversations_dir(self) -> Path:
        return self.root / "conversations"

    def _conversation_path(self, conv_id: str) -> Path:
        # Ids come from the client; keep them to one plain file name.
        safe = "".join(c for c in conv_id if c.isalnum() or c in "-_")
        return self._conversations_dir / f"{safe}.json"

    # Loading -----------------------------------------------------------------------------
    def _read_json(self, path: Path) -> Any:
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except FileNotFoundError:
            return None
        except (OSError, json.JSONDecodeError) as exc:
            # Keep the damaged file for inspection rather than overwrite it.
            broken = path.with_name(f"{path.name}.broken")
            logger.warning("Could not read %s (%s); moved it to %s", path, exc, broken.name)
            try:
                os.replace(path, broken)
            except OSError:
                pass
            return None

    def load(self) -> None:
        account = self._read_json(self._account_path) or {}
        for raw in account.get("users", []):
            user = _build(User, raw)
            self.users[user.id] = user
        for raw in account.get("tokens", []):
            token = _build(OAuthToken, raw)
            self.tokens[token.user_id] = token

        for user_id, raw in (self._read_json(self._settings_path) or {}).items():
            self.settings[user_id] = _build(UserSettings, {**raw, "user_id": user_id})

        if self._conversations_dir.is_dir():
            for path in sorted(self._conversations_dir.glob("*.json")):
                raw = self._read_json(path)
                if not isinstance(raw, dict) or "id" not in raw:
                    continue
                messages = [_build(Message, m) for m in raw.pop("messages", []) if "id" in m]
                conv = _build(Conversation, raw)
                conv.messages = sorted(messages, key=lambda m: (m.timestamp, m.id))
                self.conversations[conv.id] = conv

        self._saved = self._render()

    # Saving ------------------------------------------------------------------------------
    def _render(self) -> dict[Path, str]:
        files: dict[Path, str] = {}
        account = {
            "users": [_dump(asdict(u)) for u in self.users.values()],
            "tokens": [_dump(asdict(t)) for t in self.tokens.values()],
        }
        files[self._account_path] = json.dumps(account, indent=2)
        settings = {}
        for user_id, value in self.settings.items():
            data = _dump(asdict(value))
            data.pop("user_id", None)
            settings[user_id] = data
        files[self._settings_path] = json.dumps(settings, indent=2)
        for conv in self.conversations.values():
            conv.messages.sort(key=lambda m: (m.timestamp, m.id))
            files[self._conversation_path(conv.id)] = json.dumps(_dump(asdict(conv)), indent=2)
        return files

    async def commit(self) -> None:
        async with self._lock:
            current = self._render()
            for path, text in current.items():
                if self._saved.get(path) != text:
                    await asyncio.to_thread(_write_atomic, path, text)
            for path in set(self._saved) - set(current):
                try:
                    path.unlink()
                except FileNotFoundError:
                    pass
            self._saved = current

    def add(self, record: Any) -> None:
        if isinstance(record, User):
            self.users[record.id] = record
        elif isinstance(record, OAuthToken):
            self.tokens[record.user_id] = record
        elif isinstance(record, UserSettings):
            self.settings[record.user_id] = record
        elif isinstance(record, Conversation):
            self.conversations[record.id] = record
        elif isinstance(record, Message):
            conv = self.conversations.get(record.conversation_id)
            if conv is not None:
                conv.messages.append(record)
        else:
            raise TypeError(f"Cannot store {type(record).__name__}")

    async def delete(self, record: Any) -> None:
        if isinstance(record, Conversation):
            self.conversations.pop(record.id, None)
        elif isinstance(record, OAuthToken):
            if self.tokens.get(record.user_id) is record:
                self.tokens.pop(record.user_id, None)
        elif isinstance(record, Message):
            conv = self.conversations.get(record.conversation_id)
            if conv is not None:
                conv.messages = [m for m in conv.messages if m.id != record.id]
        else:
            raise TypeError(f"Cannot delete {type(record).__name__}")


_store: Store | None = None


def get_store() -> Store:
    global _store
    if _store is None:
        _store = Store(_app_data_dir())
        _store.load()
    return _store


async def get_db() -> AsyncGenerator[Store, None]:
    yield get_store()

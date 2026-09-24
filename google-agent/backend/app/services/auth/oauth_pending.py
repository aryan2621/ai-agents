import time
from dataclasses import dataclass
from typing import Literal

from app.models.auth import GoogleUserResponse

TTL_SECONDS = 600

_store: dict[str, "PendingEntry"] = {}


@dataclass
class PendingEntry:
    status: Literal["pending", "complete", "error"]
    created_at: float
    user: GoogleUserResponse | None = None
    error: str | None = None


def mark_pending(state: str) -> None:
    _store[state] = PendingEntry(status="pending", created_at=time.time())


def complete(state: str, user: GoogleUserResponse) -> None:
    _store[state] = PendingEntry(
        status="complete", created_at=time.time(), user=user
    )


def fail(state: str, error: str) -> None:
    _store[state] = PendingEntry(
        status="error", created_at=time.time(), error=error
    )


def get(state: str) -> PendingEntry | None:
    entry = _store.get(state)
    if entry is None:
        return None
    if time.time() - entry.created_at > TTL_SECONDS:
        _store.pop(state, None)
        return None
    return entry

from __future__ import annotations

import types

from app.services.auth.auth_service import StoredCredentials
from app.services.google.calendar import CalendarMixin
from app.services.google.docs import DocsMixin
from app.services.google.drive import DriveMixin
from app.services.google.gmail import GmailMixin
from app.services.google.sheets import SheetsMixin
from app.services.google.support import (
    _credentials,
    _google_service,
    _logged_public_method,
)


class GoogleClients(GmailMixin, CalendarMixin, DriveMixin, DocsMixin, SheetsMixin):
    def __init__(self, creds: StoredCredentials) -> None:
        self._creds = _credentials(creds)
        self._gmail = _google_service("gmail", "v1", self._creds)
        self._calendar = _google_service("calendar", "v3", self._creds)
        self._drive = _google_service("drive", "v3", self._creds)
        self._docs = _google_service("docs", "v1", self._creds)
        self._sheets = _google_service("sheets", "v4", self._creds)
        self._calendar_tz: str | None = None


for cls in GoogleClients.__mro__:
    if cls is object:
        continue
    for _method_name, _method in list(cls.__dict__.items()):
        if isinstance(_method, types.FunctionType) and not _method_name.startswith("_"):
            setattr(GoogleClients, _method_name, _logged_public_method(_method))

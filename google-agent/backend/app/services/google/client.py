from __future__ import annotations

import types

from app.services.auth.auth_service import StoredCredentials
from app.services.google.calendar import CalendarMixin
from app.services.google.docs import DocsMixin
from app.services.google.drive import DriveMixin
from app.services.google.gmail import GmailMixin
from app.services.google.sheets import SheetsMixin
from app.services.google.support import (
    _google_service,
    _logged_public_method,
)


class GoogleClients(GmailMixin, CalendarMixin, DriveMixin, DocsMixin, SheetsMixin):
    def __init__(self, creds: StoredCredentials) -> None:
        self._token = creds.google_access_token

    # Looked up when used: tools run on worker threads, each with its own cached clients.
    @property
    def _gmail(self):
        return _google_service("gmail", "v1", self._token)

    @property
    def _calendar(self):
        return _google_service("calendar", "v3", self._token)

    @property
    def _drive(self):
        return _google_service("drive", "v3", self._token)

    @property
    def _docs(self):
        return _google_service("docs", "v1", self._token)

    @property
    def _sheets(self):
        return _google_service("sheets", "v4", self._token)


for cls in GoogleClients.__mro__:
    if cls is object:
        continue
    for _method_name, _method in list(cls.__dict__.items()):
        if isinstance(_method, types.FunctionType) and not _method_name.startswith("_"):
            setattr(GoogleClients, _method_name, _logged_public_method(_method))

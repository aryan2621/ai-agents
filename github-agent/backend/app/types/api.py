from typing import Literal, TypedDict


class PermissionErrorPayload(TypedDict):
    error: str
    code: Literal["INSUFFICIENT_SCOPE"]
    agent: str
    scope: str
    label: str

from pydantic import BaseModel


class PermissionStatusResponse(BaseModel):
    id: str
    label: str
    scope: str
    granted: bool


class GitHubUserResponse(BaseModel):
    id: str
    email: str
    name: str
    picture: str
    accessToken: str
    expiresAt: int
    grantedScopes: list[str] = []
    permissions: list[PermissionStatusResponse] = []

import base64
import hashlib
import logging
import os

from cryptography.fernet import Fernet, InvalidToken

logger = logging.getLogger(__name__)


def _fernet() -> Fernet | None:
    key = os.environ.get("TOKEN_ENCRYPTION_KEY", "").strip()
    if not key:
        return None
    try:
        return Fernet(key.encode() if isinstance(key, str) else key)
    except Exception:
        derived = base64.urlsafe_b64encode(hashlib.sha256(key.encode()).digest())
        return Fernet(derived)


def encrypt_token(value: str) -> str:
    if not value:
        return value
    f = _fernet()
    if f is None:
        return value
    return f.encrypt(value.encode()).decode()


def decrypt_token(value: str) -> str:
    if not value:
        return value
    f = _fernet()
    if f is None:
        return value
    try:
        return f.decrypt(value.encode()).decode()
    except InvalidToken:
        return value

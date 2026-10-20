import base64
import hashlib
import secrets

import bcrypt
from cryptography.fernet import Fernet, InvalidToken

from app.core.config import settings

# Checked when the email is unknown so a missing account takes as long as a wrong password
_DUMMY_HASH = bcrypt.hashpw(b"dummy", bcrypt.gensalt()).decode()


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, hashed: str | None) -> bool:
    return (
        bcrypt.checkpw(password.encode(), (hashed or _DUMMY_HASH).encode()) and hashed is not None
    )


def new_token() -> str:
    return secrets.token_urlsafe(32)


def hash_token(token: str) -> str:
    """Session tokens are random, so a fast hash is enough; a DB leak reveals no usable cookie."""
    return hashlib.sha256(token.encode()).hexdigest()


def _fernet() -> Fernet:
    # ponytail: key derived from SECRET_KEY, so rotating it makes users reconnect Google.
    # Add a dedicated TOKEN_ENCRYPTION_KEY (MultiFernet) if you need rotation without that.
    key = base64.urlsafe_b64encode(hashlib.sha256(settings.secret_key.encode()).digest())
    return Fernet(key)


def encrypt_secret(value: str) -> str:
    return _fernet().encrypt(value.encode()).decode()


def decrypt_secret(value: str) -> str | None:
    try:
        return _fernet().decrypt(value.encode()).decode()
    except InvalidToken:
        return None

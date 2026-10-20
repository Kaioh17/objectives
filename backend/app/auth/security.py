import base64
import hashlib
import secrets
from datetime import timedelta
from typing import Literal

import bcrypt
import jwt
from cryptography.fernet import Fernet, InvalidToken

from app.core.config import settings
from app.core.timezone import utcnow

TokenKind = Literal["access", "refresh"]

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


def token_lifetime(kind: TokenKind) -> timedelta:
    if kind == "access":
        return timedelta(minutes=settings.access_token_minutes)
    return timedelta(days=settings.refresh_token_days)


def create_token(user_id: int, version: int, kind: TokenKind) -> str:
    """Signed JWT. `typ` stops a refresh token being used as an access token and vice versa."""
    claims = {
        "sub": str(user_id),
        "ver": version,
        "typ": kind,
        "exp": utcnow() + token_lifetime(kind),
    }
    return jwt.encode(claims, settings.secret_key, algorithm="HS256")


def decode_token(token: str, kind: TokenKind) -> dict | None:
    try:
        claims = jwt.decode(
            token, settings.secret_key, algorithms=["HS256"], options={"require": ["exp", "sub"]}
        )
    except jwt.PyJWTError:
        return None
    return claims if claims.get("typ") == kind and "ver" in claims else None


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

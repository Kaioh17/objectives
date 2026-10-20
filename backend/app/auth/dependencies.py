from typing import Annotated

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.auth.security import TokenKind, decode_token
from app.core.config import settings
from app.core.database import DBDep
from app.core.exceptions import UnauthorizedError
from app.models import User

bearer = HTTPBearer(auto_error=False)


def _user_for(db: DBDep, token: str | None, kind: TokenKind) -> User | None:
    """The active user the token belongs to, or None. A stale `ver` means it was revoked."""
    claims = decode_token(token, kind) if token else None
    user = db.get(User, int(claims["sub"])) if claims else None
    if user is None or not user.is_active or user.token_version != claims["ver"]:
        return None
    return user


def get_current_user(
    db: DBDep, credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)]
) -> User:
    user = _user_for(db, credentials.credentials if credentials else None, "access")
    if user is None:
        raise UnauthorizedError("Not signed in")
    return user


CurrentUserDep = Annotated[User, Depends(get_current_user)]


def get_refresh_user(request: Request, db: DBDep) -> User:
    user = _user_for(db, request.cookies.get(settings.refresh_cookie_name), "refresh")
    if user is None:
        raise UnauthorizedError("Not signed in")
    return user


RefreshUserDep = Annotated[User, Depends(get_refresh_user)]


def get_optional_user(request: Request, db: DBDep) -> User | None:
    """The signed-in user if there is one; never raises (used by the Google link flow).

    That flow is browser navigation, which cannot carry a Bearer header, so it reads the cookie.
    """
    return _user_for(db, request.cookies.get(settings.refresh_cookie_name), "refresh")


OptionalUserDep = Annotated[User | None, Depends(get_optional_user)]

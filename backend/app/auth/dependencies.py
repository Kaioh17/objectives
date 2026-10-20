from typing import Annotated

from fastapi import Depends, Request, Response

from app.core.config import settings
from app.core.database import DBDep
from app.core.exceptions import UnauthorizedError
from app.models import User, UserSession
from app.services import session as session_service


def get_current_session(request: Request, response: Response, db: DBDep) -> UserSession:
    token = request.cookies.get(settings.session_cookie_name)
    session = session_service.get_valid(db, token) if token else None
    if session is None or not session.user.is_active:
        raise UnauthorizedError("Not signed in")
    session_service.touch(db, session, token, response)
    return session


CurrentSessionDep = Annotated[UserSession, Depends(get_current_session)]


def get_current_user(session: CurrentSessionDep) -> User:
    return session.user


CurrentUserDep = Annotated[User, Depends(get_current_user)]


def get_optional_user(request: Request, db: DBDep) -> User | None:
    """The signed-in user if there is one; never raises (used by the Google link flow)."""
    token = request.cookies.get(settings.session_cookie_name)
    session = session_service.get_valid(db, token) if token else None
    return session.user if session and session.user.is_active else None


OptionalUserDep = Annotated[User | None, Depends(get_optional_user)]

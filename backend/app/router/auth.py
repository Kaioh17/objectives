import logging
import re
import secrets
from typing import Annotated

from fastapi import APIRouter, Query, Request, Response, status
from fastapi.responses import RedirectResponse

from app.auth import CurrentSessionDep, OptionalUserDep, new_token
from app.core.config import settings
from app.core.database import DBDep
from app.core.exceptions import AppError
from app.schemas import ErrorResponse, LoginRequest, UserCreate, UserRead
from app.services import auth as auth_service
from app.services import google
from app.services import session as session_service
from app.services import user as user_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])

# Ties the Google callback to the browser that started it
NONCE_COOKIE = "google_oauth_nonce"
NONCE_PATH = f"{settings.api_prefix}/auth/google"
# Only same-site paths: "/objectives", never "//evil.com" or "https://evil.com"
SAFE_NEXT = re.compile(r"^/(?![/\\])[\w\-./?=&%]*$")


@router.post(
    "/register",
    status_code=status.HTTP_201_CREATED,
    responses={409: {"model": ErrorResponse}},
)
def register(data: UserCreate, request: Request, response: Response, db: DBDep) -> UserRead:
    user = user_service.register(db, data)
    session_service.start(db, request, response, user)
    return user


@router.post("/login", responses={401: {"model": ErrorResponse}})
def login(data: LoginRequest, request: Request, response: Response, db: DBDep) -> UserRead:
    user = auth_service.login(db, data.email, data.password)
    session_service.start(db, request, response, user)
    return user


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(request: Request, response: Response, db: DBDep) -> None:
    """Idempotent: succeeds whether or not the cookie was still valid."""
    token = request.cookies.get(settings.session_cookie_name)
    if token and (session := session_service.get_valid(db, token)):
        session_service.revoke(db, session)
    session_service.clear_cookie(response)


@router.post(
    "/logout-all",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={401: {"model": ErrorResponse}},
)
def logout_all(session: CurrentSessionDep, response: Response, db: DBDep) -> None:
    session_service.revoke_all(db, session.user)
    session_service.clear_cookie(response)


@router.get(
    "/google/start",
    status_code=status.HTTP_302_FOUND,
    summary="Sign in with Google or connect Google Calendar",
    description="Browser navigation, not fetch. Signed out: Google login. Signed in: links Google.",
)
def google_start(
    user: OptionalUserDep,
    next: Annotated[str, Query(max_length=200)] = "/objectives",
) -> RedirectResponse:
    google.require_configured()
    nonce = new_token()
    state = google.make_state(nonce, next if SAFE_NEXT.match(next) else "/objectives")
    response = RedirectResponse(
        google.authorization_url(state, user.email if user else None),
        status_code=status.HTTP_302_FOUND,
    )
    response.set_cookie(
        NONCE_COOKIE,
        nonce,
        max_age=600,
        path=NONCE_PATH,
        httponly=True,
        secure=settings.cookie_secure,
        samesite="lax",
    )
    return response


@router.get("/google/callback", status_code=status.HTTP_302_FOUND, include_in_schema=False)
def google_callback(
    request: Request,
    user: OptionalUserDep,
    db: DBDep,
    code: str | None = None,
    state: str | None = None,
    error: str | None = None,
) -> RedirectResponse:
    def finish(path: str, signed_in_as=None) -> RedirectResponse:
        response = RedirectResponse(settings.frontend_url + path, status_code=status.HTTP_302_FOUND)
        response.delete_cookie(NONCE_COOKIE, path=NONCE_PATH)
        if signed_in_as is not None:
            session_service.start(db, request, response, signed_in_as)
        return response

    payload = google.read_state(state) if state else None
    nonce = request.cookies.get(NONCE_COOKIE)
    if not (payload and nonce and secrets.compare_digest(payload["nonce"], nonce)):
        return finish("/login?error=google_state")
    if error or not code:
        # The user pressed "Cancel" on Google's consent screen
        return finish("/login?error=google_denied" if user is None else payload["next"])

    try:
        signed_in = auth_service.google_sign_in(db, code, user)
    except AppError as exc:
        logger.warning("Google sign-in failed: %s", exc.detail)
        return finish("/login?error=google")
    # Linking from a signed-in session keeps that session; a login opens a new one
    return finish(payload["next"], None if user else signed_in)

import logging
import re
import secrets
from typing import Annotated

from fastapi import APIRouter, Query, Request, Response, status
from fastapi.responses import RedirectResponse

from app.auth import CurrentUserDep, OptionalUserDep, RefreshUserDep, new_token
from app.core.config import settings
from app.core.database import DBDep
from app.core.exceptions import AppError
from app.schemas import ErrorResponse, LoginRequest, TokenResponse, UserCreate
from app.services import auth as auth_service
from app.services import google
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
def register(data: UserCreate, response: Response, db: DBDep) -> TokenResponse:
    return auth_service.issue(response, user_service.register(db, data))


@router.post("/login", responses={401: {"model": ErrorResponse}})
def login(data: LoginRequest, response: Response, db: DBDep) -> TokenResponse:
    return auth_service.issue(response, auth_service.login(db, data.email, data.password))


@router.post(
    "/refresh",
    summary="Trade the refresh cookie for a new access token",
    description="Also issues a new refresh cookie, so the login slides forward another 30 days.",
    responses={401: {"model": ErrorResponse}},
)
def refresh(user: RefreshUserDep, response: Response) -> TokenResponse:
    return auth_service.issue(response, user)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(response: Response) -> None:
    """Idempotent. Tokens are stateless, so an access token already issued lives out its 30 min."""
    auth_service.clear_refresh_cookie(response)


@router.post(
    "/logout-all",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={401: {"model": ErrorResponse}},
)
def logout_all(user: CurrentUserDep, response: Response, db: DBDep) -> None:
    user_service.revoke_all_tokens(db, user)
    auth_service.clear_refresh_cookie(response)


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
    if not settings.google_enabled:
        # A browser navigation, so send the user back to the form instead of showing raw JSON
        return RedirectResponse(
            settings.frontend_url + "/login?error=google_unavailable",
            status_code=status.HTTP_302_FOUND,
        )
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
            auth_service.set_refresh_cookie(response, signed_in_as)
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
    # Linking while signed in keeps the existing login; a Google login sets the refresh cookie
    return finish(payload["next"], None if user else signed_in)

from datetime import timedelta

from fastapi import Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.security import create_token, encrypt_secret, token_lifetime, verify_password
from app.core.config import settings
from app.core.exceptions import ConflictError, UnauthorizedError
from app.core.timezone import utcnow
from app.models import GoogleAccount, User
from app.schemas import TokenResponse, UserRead
from app.services import google
from app.services import user as user_service

# Only auth routes (refresh, logout, the Google flow) ever need the refresh cookie
REFRESH_COOKIE_PATH = f"{settings.api_prefix}/auth"


def set_refresh_cookie(response: Response, user: User) -> None:
    """Every call issues a fresh token with a full lifetime, which is what makes the login slide."""
    response.set_cookie(
        settings.refresh_cookie_name,
        create_token(user.id, user.token_version, "refresh"),
        max_age=int(token_lifetime("refresh").total_seconds()),
        path=REFRESH_COOKIE_PATH,
        httponly=True,
        secure=settings.cookie_secure,
        samesite="lax",
    )


def clear_refresh_cookie(response: Response) -> None:
    response.delete_cookie(
        settings.refresh_cookie_name,
        path=REFRESH_COOKIE_PATH,
        httponly=True,
        secure=settings.cookie_secure,
        samesite="lax",
    )


def issue(response: Response, user: User) -> TokenResponse:
    """Start or extend a login: refresh cookie on the response, access JWT in the body."""
    set_refresh_cookie(response, user)
    return TokenResponse(
        access_token=create_token(user.id, user.token_version, "access"),
        expires_in=int(token_lifetime("access").total_seconds()),
        user=UserRead.model_validate(user),
    )


def login(db: Session, email: str, password: str) -> User:
    user = user_service.get_by_email(db, email)
    # verify_password runs even for unknown emails so timing does not reveal which exist
    valid = verify_password(password, user.hashed_password if user else None)
    if user is None or not user.is_active or not valid:
        raise UnauthorizedError("Incorrect email or password")
    return user


def google_sign_in(db: Session, code: str, current_user: User | None) -> User:
    """Finish the OAuth dance: find, link or create the user and store their Google tokens.

    With a signed-in `current_user` this links Google to that account (the "Connect calendar"
    button). Without one it is a Google login.
    """
    tokens = google.exchange_code(code)
    info = google.userinfo(tokens["access_token"])
    if not info.get("email_verified"):
        raise UnauthorizedError("Google email is not verified")

    sub = info["sub"]
    account = db.scalar(select(GoogleAccount).where(GoogleAccount.google_sub == sub))
    if account is not None:
        if current_user and account.user_id != current_user.id:
            raise ConflictError("This Google account is linked to another user")
        user = account.user
    elif current_user is not None:
        user = current_user
    else:
        user = user_service.get_by_email(db, info["email"])
        if user is None:
            user = user_service.create(db, info["email"], info.get("name"), "UTC", None)
        elif user.hashed_password:
            # The email was never verified at signup, so whoever set that password may not own
            # the address. Google just proved ownership: drop the password and every token.
            user.hashed_password = None
            user_service.revoke_all_tokens(db, user)
    if not user.is_active:
        raise UnauthorizedError("Account disabled")

    account = account or user.google_account or GoogleAccount(user=user)
    account.google_sub = sub
    account.email = info["email"]
    account.scopes = tokens.get("scope", "")
    account.access_token = encrypt_secret(tokens["access_token"])
    account.access_token_expires_at = utcnow() + timedelta(seconds=tokens.get("expires_in", 3600))
    if tokens.get("refresh_token"):
        account.refresh_token = encrypt_secret(tokens["refresh_token"])
    db.add(account)
    db.commit()
    return user

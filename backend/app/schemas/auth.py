from pydantic import EmailStr

from app.schemas.base import APIModel
from app.schemas.user import UserRead


class LoginRequest(APIModel):
    email: EmailStr
    password: str


class TokenResponse(APIModel):
    """The access JWT for the client to keep in memory; the refresh token travels as a cookie."""

    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserRead

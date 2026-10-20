from pydantic import EmailStr

from app.schemas.base import APIModel


class LoginRequest(APIModel):
    email: EmailStr
    password: str

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.security import hash_password, verify_password
from app.core.exceptions import ConflictError, ForbiddenError
from app.models import User
from app.schemas import UserCreate, UserUpdate


def get_by_email(db: Session, email: str) -> User | None:
    return db.scalar(select(User).where(User.email == email.lower()))


def create(
    db: Session, email: str, full_name: str | None, timezone: str, password: str | None
) -> User:
    if get_by_email(db, email):
        raise ConflictError("Email already registered")
    user = User(
        email=email.lower(),
        full_name=full_name,
        timezone=timezone,
        hashed_password=hash_password(password) if password else None,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def register(db: Session, data: UserCreate) -> User:
    return create(db, data.email, data.full_name, data.timezone, data.password)


def revoke_all_tokens(db: Session, user: User) -> None:
    """Every access and refresh token issued so far stops working."""
    user.token_version += 1
    db.commit()


def update(db: Session, user: User, data: UserUpdate) -> User:
    changes = data.model_dump(exclude_unset=True)
    password = changes.pop("password", None)
    current_password = changes.pop("current_password", None)
    if password:
        if user.hashed_password and not (
            current_password and verify_password(current_password, user.hashed_password)
        ):
            raise ForbiddenError("Current password is incorrect")
        user.hashed_password = hash_password(password)
        # A new password logs out every device; the caller re-issues the cookie for this one
        user.token_version += 1
    for field, value in changes.items():
        if value is not None:
            setattr(user, field, value)
    db.commit()
    db.refresh(user)
    return user


def delete(db: Session, user: User) -> None:
    db.delete(user)
    db.commit()

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.security import hash_password, verify_password
from app.core.exceptions import ConflictError, ForbiddenError
from app.models import User
from app.schemas import UserCreate, UserUpdate
from app.services import session as session_service


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


def update(db: Session, user: User, data: UserUpdate, keep_session_id: int) -> User:
    changes = data.model_dump(exclude_unset=True)
    password = changes.pop("password", None)
    current_password = changes.pop("current_password", None)
    if password:
        if user.hashed_password and not (
            current_password and verify_password(current_password, user.hashed_password)
        ):
            raise ForbiddenError("Current password is incorrect")
        user.hashed_password = hash_password(password)
    for field, value in changes.items():
        if value is not None:
            setattr(user, field, value)
    db.commit()
    if password:
        # A new password logs out every other device
        session_service.revoke_all(db, user, keep_id=keep_session_id)
    db.refresh(user)
    return user


def delete(db: Session, user: User) -> None:
    db.delete(user)
    db.commit()

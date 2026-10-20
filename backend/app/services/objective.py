import logging

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions import AppError, NotFoundError
from app.models import Mode, Objective, User
from app.schemas import ObjectiveCreate, ObjectiveUpdate
from app.services import calendar as calendar_service

logger = logging.getLogger(__name__)

# ponytail: one user's objectives fit in a single response; paginate if that stops being true
MAX_LISTED = 500


def list_for_user(
    db: Session, user: User, archived: bool | None, mode: Mode | None
) -> list[Objective]:
    stmt = select(Objective).where(Objective.user_id == user.id)
    if archived is not None:
        stmt = stmt.where(Objective.archived == archived)
    if mode is not None:
        stmt = stmt.where(Objective.mode == mode)
    stmt = stmt.order_by(Objective.created_at.desc(), Objective.id.desc()).limit(MAX_LISTED)
    return list(db.scalars(stmt))


def get_owned(db: Session, user: User, objective_id: int) -> Objective:
    # Filtering by user_id means another user's id looks exactly like a missing one
    objective = db.scalar(
        select(Objective).where(Objective.id == objective_id, Objective.user_id == user.id)
    )
    if objective is None:
        raise NotFoundError("Objective not found")
    return objective


def create(db: Session, user: User, data: ObjectiveCreate) -> Objective:
    objective = Objective(user=user, **data.model_dump())
    db.add(objective)
    db.commit()
    db.refresh(objective)
    return objective


def update(db: Session, objective: Objective, data: ObjectiveUpdate) -> Objective:
    # Every updatable column is NOT NULL, so an explicit null means "leave it"
    for field, value in data.model_dump(exclude_unset=True).items():
        if value is not None:
            setattr(objective, field, value)
    db.commit()
    db.refresh(objective)
    return objective


def delete(db: Session, user: User, objective: Objective) -> None:
    if objective.event_id:
        try:
            calendar_service.remove_event(db, user, objective)
        except AppError as exc:
            # The objective is going away regardless; a stale Google event is the lesser harm
            logger.warning("Left Google event %s behind: %s", objective.event_id, exc.detail)
    db.delete(objective)
    db.commit()

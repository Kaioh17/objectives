from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from app.auth import CurrentUserDep, get_current_user
from app.core.database import DBDep
from app.models import Mode
from app.schemas import (
    ErrorResponse,
    ObjectiveCreate,
    ObjectiveRead,
    ObjectiveUpdate,
    ScheduleRequest,
)
from app.services import calendar as calendar_service
from app.services import objective as objective_service

router = APIRouter(
    prefix="/objectives",
    tags=["objectives"],
    dependencies=[Depends(get_current_user)],
    responses={401: {"model": ErrorResponse}},
)


@router.get("")
def list_objectives(
    user: CurrentUserDep,
    db: DBDep,
    archived: Annotated[bool | None, Query()] = None,
    mode: Annotated[Mode | None, Query()] = None,
) -> list[ObjectiveRead]:
    return objective_service.list_for_user(db, user, archived, mode)  # type: ignore[return-value]


@router.post("", status_code=status.HTTP_201_CREATED)
def create_objective(data: ObjectiveCreate, user: CurrentUserDep, db: DBDep) -> ObjectiveRead:
    return objective_service.create(db, user, data)


@router.get("/{objective_id}", responses={404: {"model": ErrorResponse}})
def read_objective(objective_id: int, user: CurrentUserDep, db: DBDep) -> ObjectiveRead:
    return objective_service.get_owned(db, user, objective_id)


@router.patch("/{objective_id}", responses={404: {"model": ErrorResponse}})
def update_objective(
    objective_id: int, data: ObjectiveUpdate, user: CurrentUserDep, db: DBDep
) -> ObjectiveRead:
    objective = objective_service.get_owned(db, user, objective_id)
    return objective_service.update(db, objective, data)


@router.delete(
    "/{objective_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={404: {"model": ErrorResponse}},
)
def delete_objective(objective_id: int, user: CurrentUserDep, db: DBDep) -> None:
    objective = objective_service.get_owned(db, user, objective_id)
    objective_service.delete(db, user, objective)


@router.post(
    "/{objective_id}/schedule",
    summary="Add the objective to Google Calendar, or move its event",
    responses={404: {"model": ErrorResponse}, 409: {"model": ErrorResponse}},
)
def schedule_objective(
    objective_id: int, data: ScheduleRequest, user: CurrentUserDep, db: DBDep
) -> ObjectiveRead:
    objective = objective_service.get_owned(db, user, objective_id)
    return calendar_service.schedule(db, user, objective, data)


@router.delete(
    "/{objective_id}/schedule",
    summary="Remove the objective's Google Calendar event",
    responses={404: {"model": ErrorResponse}, 409: {"model": ErrorResponse}},
)
def unschedule_objective(objective_id: int, user: CurrentUserDep, db: DBDep) -> ObjectiveRead:
    objective = objective_service.get_owned(db, user, objective_id)
    return calendar_service.unschedule(db, user, objective)

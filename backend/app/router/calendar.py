from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from app.auth import CurrentUserDep, get_current_user
from app.core.database import DBDep
from app.schemas import CalendarStatus, ErrorResponse, ScheduleItem
from app.services import calendar as calendar_service

router = APIRouter(
    prefix="/calendar",
    tags=["calendar"],
    dependencies=[Depends(get_current_user)],
    responses={401: {"model": ErrorResponse}},
)


@router.get("/status", summary="Is Google Calendar connected?")
def calendar_status(user: CurrentUserDep, db: DBDep) -> CalendarStatus:
    return calendar_service.status(db, user)


@router.get(
    "/events",
    summary="The user's Google events for one local day",
    responses={409: {"model": ErrorResponse}, 502: {"model": ErrorResponse}},
)
def list_events(
    user: CurrentUserDep,
    db: DBDep,
    day: Annotated[date, Query(alias="date", description="Local day, YYYY-MM-DD")],
) -> list[ScheduleItem]:
    return calendar_service.list_day(db, user, day)


@router.post("/disconnect", status_code=status.HTTP_204_NO_CONTENT)
def disconnect(user: CurrentUserDep, db: DBDep) -> None:
    calendar_service.disconnect(db, user)

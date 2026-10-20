from fastapi import APIRouter, Depends, Response, status

from app.auth import CurrentSessionDep, CurrentUserDep, get_current_user
from app.core.database import DBDep
from app.schemas import ErrorResponse, UserRead, UserUpdate
from app.services import session as session_service
from app.services import user as user_service

# Users only ever act on themselves, so there is no /users/{id}
router = APIRouter(
    prefix="/users",
    tags=["users"],
    dependencies=[Depends(get_current_user)],
    responses={401: {"model": ErrorResponse}},
)


@router.get("/me")
def read_me(current_user: CurrentUserDep) -> UserRead:
    return current_user


@router.patch("/me", responses={403: {"model": ErrorResponse}})
def update_me(data: UserUpdate, session: CurrentSessionDep, db: DBDep) -> UserRead:
    return user_service.update(db, session.user, data, keep_session_id=session.id)


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
def delete_me(current_user: CurrentUserDep, response: Response, db: DBDep) -> None:
    user_service.delete(db, current_user)
    session_service.clear_cookie(response)

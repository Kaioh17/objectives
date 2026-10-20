from fastapi import APIRouter, Depends, Response, status

from app.auth import CurrentUserDep, get_current_user
from app.core.database import DBDep
from app.schemas import ErrorResponse, UserRead, UserUpdate
from app.services import auth as auth_service
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
def update_me(
    data: UserUpdate, current_user: CurrentUserDep, response: Response, db: DBDep
) -> UserRead:
    user = user_service.update(db, current_user, data)
    if data.password:
        # Keeps this device signed in. Its old access token is revoked, so it calls /auth/refresh
        auth_service.set_refresh_cookie(response, user)
    return user


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
def delete_me(current_user: CurrentUserDep, response: Response, db: DBDep) -> None:
    user_service.delete(db, current_user)
    auth_service.clear_refresh_cookie(response)

from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from ...core.auth import require_admin
from ...core.database import get_session
from . import service
from .schemas import (
    ChangeUserPasswordRequest,
    CreateUserRequest,
    ErrorItem,
    StandardErrorResponse,
    UpdateUserRequest,
    UserDeleteResponse,
    UserResponse,
    UserSuccessResponse,
    UsersListResponse,
)

router = APIRouter(prefix="/api/v1/users", tags=["users"])


def _error_response(message: str, field: str | None, status_code: int):
    error = StandardErrorResponse(
        success=False,
        message=message,
        errors=[ErrorItem(field=field, detail=message)],
    )
    return JSONResponse(status_code=status_code, content=error.dict())


@router.post(
    "",
    response_model=UserSuccessResponse,
    responses={400: {"model": StandardErrorResponse}},
    dependencies=[Depends(require_admin)],
)
def create_user(
    payload: CreateUserRequest,
    session: Session = Depends(get_session),
    current_user=Depends(require_admin),
) -> UserSuccessResponse:
    try:
        user = service.create_user(payload, session, modified_by=current_user.username)
    except service.UserError as exc:
        return _error_response(exc.message, exc.field, status.HTTP_400_BAD_REQUEST)

    return UserSuccessResponse(
        success=True,
        message="User created successfully.",
        data=UserResponse.model_validate(user, from_attributes=True),
    )


@router.get("", response_model=UsersListResponse, dependencies=[Depends(require_admin)])
def list_users(session: Session = Depends(get_session)) -> UsersListResponse:
    users = service.list_users(session)
    serialized_users = [
        UserResponse.model_validate(user, from_attributes=True) for user in users
    ]
    return UsersListResponse(
        success=True,
        message="Users retrieved successfully.",
        data=serialized_users,
    )


@router.get(
    "/{user_id}",
    response_model=UserSuccessResponse,
    responses={404: {"model": StandardErrorResponse}},
    dependencies=[Depends(require_admin)],
)
def get_user(user_id: str, session: Session = Depends(get_session)):
    try:
        user = service.get_user(user_id, session)
    except service.UserError as exc:
        return _error_response(exc.message, exc.field, status.HTTP_404_NOT_FOUND)

    return UserSuccessResponse(
        success=True,
        message="User retrieved successfully.",
        data=UserResponse.model_validate(user, from_attributes=True),
    )


@router.put(
    "/{user_id}",
    response_model=UserSuccessResponse,
    responses={400: {"model": StandardErrorResponse}, 404: {"model": StandardErrorResponse}},
    dependencies=[Depends(require_admin)],
)
def update_user(
    user_id: str,
    payload: UpdateUserRequest,
    session: Session = Depends(get_session),
    current_user=Depends(require_admin),
) -> UserSuccessResponse:
    try:
        user = service.update_user(
            user_id, payload, session, modified_by=current_user.username
        )
    except service.UserError as exc:
        status_code = (
            status.HTTP_404_NOT_FOUND if exc.field == "user_id" else status.HTTP_400_BAD_REQUEST
        )
        return _error_response(exc.message, exc.field, status_code)

    return UserSuccessResponse(
        success=True,
        message="User updated successfully.",
        data=UserResponse.model_validate(user, from_attributes=True),
    )


@router.put(
    "/{user_id}/password",
    response_model=UserSuccessResponse,
    responses={400: {"model": StandardErrorResponse}, 404: {"model": StandardErrorResponse}},
    dependencies=[Depends(require_admin)],
)
def change_password(
    user_id: str,
    payload: ChangeUserPasswordRequest,
    session: Session = Depends(get_session),
    current_user=Depends(require_admin),
) -> UserSuccessResponse:
    try:
        user = service.change_password(
            user_id, payload, session, modified_by=current_user.username
        )
    except service.UserError as exc:
        status_code = (
            status.HTTP_404_NOT_FOUND if exc.field == "user_id" else status.HTTP_400_BAD_REQUEST
        )
        return _error_response(exc.message, exc.field, status_code)

    return UserSuccessResponse(
        success=True,
        message="User password updated successfully.",
        data=UserResponse.model_validate(user, from_attributes=True),
    )


@router.delete(
    "/{user_id}",
    response_model=UserDeleteResponse,
    responses={404: {"model": StandardErrorResponse}},
    dependencies=[Depends(require_admin)],
)
def delete_user(
    user_id: str,
    session: Session = Depends(get_session),
    current_user=Depends(require_admin),
) -> UserDeleteResponse:
    try:
        service.delete_user(user_id, session, modified_by=current_user.username)
    except service.UserError as exc:
        return _error_response(exc.message, exc.field, status.HTTP_404_NOT_FOUND)

    return UserDeleteResponse(
        success=True,
        message="User deleted successfully.",
        data=None,
    )

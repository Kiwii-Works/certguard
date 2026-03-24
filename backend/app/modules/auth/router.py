from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from ...core.auth import get_current_user
from ...core.database import get_session
from . import service
from .schemas import (
    AuthenticatedUserResponse,
    CurrentUserResponse,
    ErrorItem,
    LoginRequest,
    LoginResponse,
    LogoutResponse,
    StandardErrorResponse,
)

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


@router.post(
    "/login",
    response_model=LoginResponse,
    responses={401: {"model": StandardErrorResponse}},
)
def login(payload: LoginRequest, session: Session = Depends(get_session)):
    try:
        data = service.login(payload, session)
    except service.AuthError as exc:
        error_response = StandardErrorResponse(
            success=False,
            message="Validation failed.",
            errors=[ErrorItem(field=exc.field, detail=exc.message)],
        )
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content=error_response.dict(),
        )

    return LoginResponse(
        success=True,
        message="Login completed successfully.",
        data=data,
    )


@router.get("/me", response_model=CurrentUserResponse)
def get_current_user_route(user=Depends(get_current_user)) -> CurrentUserResponse:
    return CurrentUserResponse(
        success=True,
        message="Current user retrieved successfully.",
        data=AuthenticatedUserResponse.model_validate(user, from_attributes=True),
    )


@router.post("/logout", response_model=LogoutResponse)
def logout(
    session: Session = Depends(get_session),
    current_user=Depends(get_current_user),
) -> LogoutResponse:
    service.logout(
        session=session,
        modified_by=current_user.username,
        user_id=current_user.id,
    )
    return LogoutResponse(
        success=True,
        message="Logout completed successfully.",
        data=None,
    )

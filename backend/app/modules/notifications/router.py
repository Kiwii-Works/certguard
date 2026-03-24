from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from ...core.auth import require_admin
from ...core.database import get_session
from . import service
from .schemas import (
    ErrorItem,
    NotificationSettingsEnvelope,
    NotificationTestResponse,
    StandardErrorResponse,
    UpdateNotificationSettingsRequest,
)

router = APIRouter(prefix="/api/v1/notifications", tags=["notifications"])


def _error_response(message: str, field: str | None, status_code: int):
    error = StandardErrorResponse(
        success=False,
        message=message,
        errors=[ErrorItem(field=field, detail=message)],
    )
    return JSONResponse(status_code=status_code, content=error.dict())


@router.get(
    "/settings",
    response_model=NotificationSettingsEnvelope,
    responses={404: {"model": StandardErrorResponse}},
    dependencies=[Depends(require_admin)],
)
def get_settings(session: Session = Depends(get_session)):
    try:
        settings = service.get_settings(session)
    except service.NotificationError as exc:
        return _error_response(exc.message, exc.field, status.HTTP_404_NOT_FOUND)

    return NotificationSettingsEnvelope(
        success=True,
        message="Notification settings retrieved successfully.",
        data=settings,
    )


@router.put(
    "/settings",
    response_model=NotificationSettingsEnvelope,
    responses={400: {"model": StandardErrorResponse}},
    dependencies=[Depends(require_admin)],
)
def update_settings(
    payload: UpdateNotificationSettingsRequest,
    session: Session = Depends(get_session),
    current_user=Depends(require_admin),
):
    settings = service.update_settings(
        payload, session, modified_by=current_user.username
    )
    return NotificationSettingsEnvelope(
        success=True,
        message="Notification settings updated successfully.",
        data=settings,
    )


@router.post(
    "/test",
    response_model=NotificationTestResponse,
    dependencies=[Depends(require_admin)],
)
def test_notification(
    session: Session = Depends(get_session),
    current_user=Depends(require_admin),
) -> NotificationTestResponse:
    service.send_test_notification(session, modified_by=current_user.username)
    return NotificationTestResponse(
        success=True,
        message="Test notification sent successfully.",
        data=None,
    )

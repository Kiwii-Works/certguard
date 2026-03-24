from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from ...core.auth import require_admin
from ...core.database import get_session
from . import service
from .schemas import ErrorItem, StandardErrorResponse, TransactionLogsListResponse

router = APIRouter(prefix="/api/v1/logs", tags=["logs"])


def _error_response(message: str, field: str | None, status_code: int):
    error = StandardErrorResponse(
        success=False,
        message=message,
        errors=[ErrorItem(field=field, detail=message)],
    )
    return JSONResponse(status_code=status_code, content=error.dict())


@router.get(
    "/transactions",
    response_model=TransactionLogsListResponse,
    dependencies=[Depends(require_admin)],
)
def list_transactions(
    action_type: str | None = None,
    entity_domain: str | None = None,
    modified_by: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    session: Session = Depends(get_session),
):
    try:
        logs = service.list_logs(
            action_type=action_type,
            entity_domain=entity_domain,
            modified_by=modified_by,
            date_from=date_from,
            date_to=date_to,
            session=session,
        )
    except service.LogsError as exc:
        return _error_response(exc.message, exc.field, status.HTTP_400_BAD_REQUEST)

    return TransactionLogsListResponse(
        success=True,
        message="Transaction logs retrieved successfully.",
        data=logs,
    )

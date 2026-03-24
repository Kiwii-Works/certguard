from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ...core.auth import get_current_user
from ...core.database import get_session
from . import service
from .schemas import DashboardSummaryResponse, DashboardSummaryData

router = APIRouter(prefix="/api/v1/dashboard", tags=["dashboard"])


@router.get(
    "/summary",
    response_model=DashboardSummaryResponse,
    dependencies=[Depends(get_current_user)],
)
def get_summary(session: Session = Depends(get_session)) -> DashboardSummaryResponse:
    summary = service.get_summary(session)
    return DashboardSummaryResponse(
        success=True,
        message="Dashboard summary retrieved successfully.",
        data=DashboardSummaryData(**summary),
    )

from pydantic import BaseModel


class DashboardSummaryData(BaseModel):
    total_certificates: int
    expiring_soon_certificates: int
    active_users: int


class DashboardSummaryResponse(BaseModel):
    success: bool = True
    message: str
    data: DashboardSummaryData

from datetime import datetime
from typing import Any, List, Optional

from pydantic import BaseModel


class ErrorItem(BaseModel):
    field: Optional[str]
    detail: str


class StandardErrorResponse(BaseModel):
    success: bool = False
    message: str
    errors: List[ErrorItem]


class TransactionLogDetailResponse(BaseModel):
    uid: int
    entity_domain: str
    entity_id: str
    transaction_description: str
    changes: Any | None


class TransactionLogResponse(BaseModel):
    transaction_uid: str
    action_type: str
    transaction_date: datetime
    transaction_date_utc: datetime
    modified_by: str
    details: List[TransactionLogDetailResponse]

    class Config:
        orm_mode = True


class TransactionLogsListResponse(BaseModel):
    success: bool = True
    message: str
    data: List[TransactionLogResponse]

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, EmailStr


class ErrorItem(BaseModel):
    field: Optional[str]
    detail: str


class StandardErrorResponse(BaseModel):
    success: bool = False
    message: str
    errors: List[ErrorItem]


class NotificationSettingsResponse(BaseModel):
    enabled: bool
    recipient_emails: List[EmailStr]
    days_before_expiration: int
    send_time: str
    send_days: List[str]
    from_email: EmailStr
    subject_template: str
    body_template: str
    attachment_file_name_template: Optional[str]
    created_at: datetime | None = None
    updated_at: datetime | None = None

    class Config:
        orm_mode = True


class NotificationSettingsEnvelope(BaseModel):
    success: bool = True
    message: str
    data: NotificationSettingsResponse


class UpdateNotificationSettingsRequest(BaseModel):
    enabled: bool
    recipient_emails: List[EmailStr]
    days_before_expiration: int
    send_time: str
    send_days: List[str]
    from_email: EmailStr
    subject_template: str
    body_template: str
    attachment_file_name_template: Optional[str]


class NotificationTestResponse(BaseModel):
    success: bool = True
    message: str
    data: None = None

from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Integer, String, func
from sqlalchemy.dialects.sqlite import JSON

from ...core.database import Base


class NotificationSettings(Base):
    __tablename__ = "notification_settings"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    enabled = Column(Boolean, default=True, nullable=False)
    recipient_emails = Column(JSON, nullable=False)
    days_before_expiration = Column(Integer, nullable=False)
    send_time = Column(String, nullable=False)
    send_days = Column(JSON, nullable=False)
    from_email = Column(String, nullable=False)
    subject_template = Column(String, nullable=False)
    body_template = Column(String, nullable=False)
    attachment_file_name_template = Column(String, nullable=True)
    created_at = Column(DateTime, server_default=func.utc.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.utc.now(), nullable=False)

from datetime import datetime

from sqlalchemy import Boolean, Column, Date, DateTime, Integer, String

from ...core.database import Base


class Certificate(Base):
    __tablename__ = "certificates"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    certificate = Column(String, unique=True, nullable=False)
    security_token_value = Column(String, nullable=True)
    used_by = Column(String, nullable=True)
    environment = Column(String, nullable=True)
    expiration_date = Column(Date, nullable=False)
    is_deleted = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

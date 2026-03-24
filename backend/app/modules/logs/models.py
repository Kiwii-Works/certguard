from datetime import datetime

from sqlalchemy import JSON, Column, DateTime, Integer, String

from ...core.database import Base


class TransactionLog(Base):
    __tablename__ = "transaction_logs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    transaction_uid = Column(String, unique=True, nullable=False)
    action_type = Column(String, nullable=False)
    transaction_date = Column(DateTime, nullable=False)
    transaction_date_utc = Column(DateTime, nullable=False)
    modified_by = Column(String, nullable=False)
    details = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

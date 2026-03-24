from datetime import datetime

from sqlalchemy.orm import Session

from .models import TransactionLog


def list_transaction_logs(
    session: Session,
    action_type: str | None,
    entity_domain: str | None,
    modified_by: str | None,
    date_from: datetime | None,
    date_to: datetime | None,
) -> list[TransactionLog]:
    query = session.query(TransactionLog)

    if action_type:
        query = query.filter(TransactionLog.action_type == action_type)
    if modified_by:
        query = query.filter(TransactionLog.modified_by == modified_by)
    if date_from:
        query = query.filter(TransactionLog.transaction_date_utc >= date_from)
    if date_to:
        query = query.filter(TransactionLog.transaction_date_utc <= date_to)
    return query.order_by(TransactionLog.transaction_date_utc.desc()).all()


def create_transaction_log(session: Session, log: TransactionLog) -> TransactionLog:
    session.add(log)
    session.commit()
    session.refresh(log)
    return log

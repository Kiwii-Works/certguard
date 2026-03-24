from sqlalchemy.orm import Session

from . import repository


def get_summary(session: Session):
    return repository.get_dashboard_summary(session)

from datetime import date, timedelta

from sqlalchemy.orm import Session

from ..certificates.repository import count_certificates, count_expiring_soon
from ..users.repository import count_active_users


def get_dashboard_summary(session: Session, expiring_within_days: int = 30) -> dict[str, int]:
    cutoff_date = date.today() + timedelta(days=expiring_within_days)
    return {
        "total_certificates": count_certificates(session),
        "expiring_soon_certificates": count_expiring_soon(session, cutoff_date),
        "active_users": count_active_users(session),
    }

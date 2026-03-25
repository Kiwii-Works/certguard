from .config import get_settings
from .database import SessionLocal, create_all
from .scheduler import schedule_notification_job, start_scheduler
from .security import hash_password
from ..modules.notifications.repository import get_settings as get_notification_settings
from ..modules.users.repository import count_users, create_user


def initialize_app() -> None:
    get_settings()
    create_all()

    start_scheduler()

    session = SessionLocal()
    try:
        if count_users(session) == 0:
            create_user(
                session=session,
                username="admin",
                email="admin@certguard.local",
                password_hash=hash_password("Admin123!"),
                role="admin",
                is_active=True,
            )

        settings = get_notification_settings(session)
        if settings:
            schedule_notification_job(
                _parse_send_time(settings.send_time)
            )
    finally:
        session.close()


def _parse_send_time(value: str):
    hour, minute = value.split(":")
    from datetime import time

    return time(hour=int(hour), minute=int(minute))

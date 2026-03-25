from datetime import time

from apscheduler.schedulers.background import BackgroundScheduler

from .database import SessionLocal

_SCHEDULER: BackgroundScheduler | None = None
_NOTIFICATION_JOB_ID = "notification-send"


def _get_scheduler() -> BackgroundScheduler:
    global _SCHEDULER
    if _SCHEDULER is None:
        _SCHEDULER = BackgroundScheduler()
    return _SCHEDULER


def start_scheduler() -> None:
    scheduler = _get_scheduler()
    if not scheduler.running:
        scheduler.start()


def shutdown_scheduler() -> None:
    scheduler = _get_scheduler()
    if scheduler.running:
        scheduler.shutdown(wait=False)


def _run_notification_job():
    from ..modules.notifications.service import run_scheduled_notifications

    session = SessionLocal()
    try:
        run_scheduled_notifications(session)
    finally:
        session.close()


def schedule_notification_job(send_time: time) -> None:
    scheduler = _get_scheduler()
    if scheduler.get_job(_NOTIFICATION_JOB_ID):
        scheduler.remove_job(_NOTIFICATION_JOB_ID)

    scheduler.add_job(
        _run_notification_job,
        "cron",
        id=_NOTIFICATION_JOB_ID,
        hour=send_time.hour,
        minute=send_time.minute,
        replace_existing=True,
    )

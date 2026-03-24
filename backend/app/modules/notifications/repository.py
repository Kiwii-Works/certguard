from sqlalchemy.orm import Session

from .models import NotificationSettings


def get_settings(session: Session) -> NotificationSettings | None:
    return session.query(NotificationSettings).order_by(NotificationSettings.id).first()


def save_settings(session: Session, settings: NotificationSettings) -> NotificationSettings:
    session.add(settings)
    session.commit()
    session.refresh(settings)
    return settings

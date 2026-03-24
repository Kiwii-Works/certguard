from . import repository
from ..logs import service as logs_service
from .models import NotificationSettings
from .schemas import UpdateNotificationSettingsRequest


class NotificationError(Exception):
    def __init__(self, message: str, field: str | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.field = field


def get_settings(session):
    settings = repository.get_settings(session)
    if settings is None:
        raise NotificationError("Notification settings not found.")
    return settings


def update_settings(payload: UpdateNotificationSettingsRequest, session, modified_by: str):
    settings = repository.get_settings(session)
    if settings is None:
        settings = NotificationSettings()

    before = {
        "enabled": settings.enabled,
        "recipient_emails": settings.recipient_emails,
        "days_before_expiration": settings.days_before_expiration,
        "send_time": settings.send_time,
        "send_days": settings.send_days,
        "from_email": settings.from_email,
        "subject_template": settings.subject_template,
        "body_template": settings.body_template,
        "attachment_file_name_template": settings.attachment_file_name_template,
    }

    settings.enabled = payload.enabled
    settings.recipient_emails = [str(email) for email in payload.recipient_emails]
    settings.days_before_expiration = payload.days_before_expiration
    settings.send_time = payload.send_time
    settings.send_days = payload.send_days
    settings.from_email = str(payload.from_email)
    settings.subject_template = payload.subject_template
    settings.body_template = payload.body_template
    settings.attachment_file_name_template = payload.attachment_file_name_template

    updated = repository.save_settings(session, settings)
    logs_service.create_log(
        session=session,
        action_type="update_notification_settings",
        modified_by=modified_by,
        details=[
            {
                "uid": 1,
                "entity_domain": "notification",
                "entity_id": "settings",
                "transaction_description": "Updated notification settings.",
                "changes": {
                    "before": before,
                    "after": {
                        "enabled": updated.enabled,
                        "recipient_emails": updated.recipient_emails,
                        "days_before_expiration": updated.days_before_expiration,
                        "send_time": updated.send_time,
                        "send_days": updated.send_days,
                        "from_email": updated.from_email,
                        "subject_template": updated.subject_template,
                        "body_template": updated.body_template,
                        "attachment_file_name_template": updated.attachment_file_name_template,
                    },
                },
            }
        ],
    )
    return updated


def send_test_notification(session, modified_by: str) -> None:
    logs_service.create_log(
        session=session,
        action_type="test_notification",
        modified_by=modified_by,
        details=[
            {
                "uid": 1,
                "entity_domain": "notification",
                "entity_id": "test",
                "transaction_description": "Sent test notification.",
                "changes": None,
            }
        ],
    )
    return None

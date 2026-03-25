from datetime import datetime
from uuid import uuid4

from . import repository
from .models import TransactionLog


class LogsError(Exception):
    def __init__(self, message: str, field: str | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.field = field


_ALLOWED_ENTITY_DOMAINS = {"user", "certificate", "import", "auth", "notification"}
_ALLOWED_ACTION_TYPES = {
    "login",
    "logout",
    "create_user",
    "update_user",
    "change_user_password",
    "delete_user",
    "create_certificate",
    "update_certificate",
    "delete_certificate",
    "import_certificates",
    "update_notification_settings",
    "test_notification",
    "send_notification",
}


def _parse_datetime(value: str | None, field: str) -> datetime | None:
    if not value:
        return None
    try:
        if value.endswith("Z"):
            value = value.replace("Z", "+00:00")
        return datetime.fromisoformat(value)
    except ValueError as exc:
        raise LogsError("Invalid datetime format.", field=field) from exc


def list_logs(
    action_type: str | None,
    entity_domain: str | None,
    modified_by: str | None,
    date_from: str | None,
    date_to: str | None,
    session,
):
    parsed_from = _parse_datetime(date_from, "date_from")
    parsed_to = _parse_datetime(date_to, "date_to")

    if entity_domain and entity_domain not in _ALLOWED_ENTITY_DOMAINS:
        raise LogsError("Invalid entity_domain.", field="entity_domain")
    if action_type and action_type not in _ALLOWED_ACTION_TYPES:
        raise LogsError("Invalid action_type.", field="action_type")

    logs = repository.list_transaction_logs(
        session,
        action_type=action_type,
        entity_domain=entity_domain,
        modified_by=modified_by,
        date_from=parsed_from,
        date_to=parsed_to,
    )

    if not entity_domain:
        return logs

    filtered = []
    for log in logs:
        details = log.details or []
        if any(detail.get("entity_domain") == entity_domain for detail in details):
            filtered.append(log)
    return filtered


def create_log(
    session,
    action_type: str,
    modified_by: str,
    details: list[dict],
):
    if action_type not in _ALLOWED_ACTION_TYPES:
        raise LogsError("Invalid action_type.", field="action_type")
    now = datetime.utcnow()
    log = TransactionLog(
        transaction_uid=str(uuid4()),
        action_type=action_type,
        transaction_date=now,
        transaction_date_utc=now,
        modified_by=modified_by,
        details=details,
    )
    repository.create_transaction_log(session, log)

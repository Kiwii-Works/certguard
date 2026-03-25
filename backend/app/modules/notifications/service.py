import csv
from datetime import date, datetime, time, timedelta
from io import StringIO
import re
import smtplib

from email.message import EmailMessage
from email.utils import formataddr
import html
import smtplib

from . import repository
from ..certificates.repository import list_expiring_within_days
from ..logs import service as logs_service
from ...core.config import get_settings as get_app_settings
from ...core.scheduler import schedule_notification_job
from .models import NotificationSettings
from .schemas import UpdateNotificationSettingsRequest


class NotificationError(Exception):
    def __init__(self, message: str, field: str | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.field = field

_ALLOWED_SEND_DAYS = {
    "monday",
    "tuesday",
    "wednesday",
    "thursday",
    "friday",
    "saturday",
    "sunday",
}
_ALLOWED_PLACEHOLDERS = {
    "process_date",
    "days_before_expiration",
    "expiring_certificates_count",
}
_TIME_PATTERN = re.compile(r"^\d{2}:\d{2}$")


def get_settings(session):
    settings = repository.get_settings(session)
    if settings is None:
        raise NotificationError("Notification settings not found.")
    return settings


def _validate_settings(payload: UpdateNotificationSettingsRequest) -> list[str]:
    normalized_days = [day.strip().lower() for day in payload.send_days]
    if payload.days_before_expiration < 1:
        raise NotificationError(
            "days_before_expiration must be greater than or equal to 1.",
            field="days_before_expiration",
        )
    if not _TIME_PATTERN.match(payload.send_time):
        raise NotificationError("send_time must follow HH:MM.", field="send_time")
    for day in normalized_days:
        if day not in _ALLOWED_SEND_DAYS:
            raise NotificationError("Invalid send_day value.", field="send_days")
    _validate_template(payload.subject_template, "subject_template")
    _validate_template(payload.body_template, "body_template")
    if payload.attachment_file_name_template:
        _validate_template(
            payload.attachment_file_name_template,
            "attachment_file_name_template",
        )
    return normalized_days


def _validate_template(template: str, field: str) -> None:
    for match in re.findall(r"{([^}]+)}", template):
        if match not in _ALLOWED_PLACEHOLDERS:
            raise NotificationError("Invalid template placeholder.", field=field)


def update_settings(payload: UpdateNotificationSettingsRequest, session, modified_by: str):
    normalized_days = _validate_settings(payload)
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
    settings.send_days = normalized_days
    settings.from_email = str(payload.from_email)
    settings.subject_template = payload.subject_template
    settings.body_template = payload.body_template
    settings.attachment_file_name_template = payload.attachment_file_name_template

    updated = repository.save_settings(session, settings)
    schedule_notification_job(_parse_time(updated.send_time))
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
    settings = repository.get_settings(session)
    if settings is None:
        raise NotificationError("Notification settings not found.")
    if not settings.enabled:
        raise NotificationError("Notifications are disabled.")

    subject = _render_template(
        settings.subject_template,
        process_date=date.today(),
        days_before_expiration=settings.days_before_expiration,
        expiring_certificates_count=0,
    )
    body = _render_template(
        settings.body_template,
        process_date=date.today(),
        days_before_expiration=settings.days_before_expiration,
        expiring_certificates_count=0,
    )
    _send_email(
        settings=settings,
        subject=subject,
        body=body,
        attachment_name=None,
        attachment_csv=None,
    )

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


def run_scheduled_notifications(session) -> None:
    settings = repository.get_settings(session)
    if settings is None or not settings.enabled:
        return

    today = date.today()
    today_day = today.strftime("%A").lower()
    send_days = [day.strip().lower() for day in (settings.send_days or [])]
    
    if send_days and today_day not in send_days:
        return

    cutoff_date = today + timedelta(days=settings.days_before_expiration)
    expiring = list_expiring_within_days(session, cutoff_date)
    expiring.sort(key=lambda c: (c.expiration_date - today).days)

    subject = _render_template(
        settings.subject_template,
        process_date=today,
        days_before_expiration=settings.days_before_expiration,
        expiring_certificates_count=len(expiring),
    )
    body = _render_template(
        settings.body_template,
        process_date=today,
        days_before_expiration=settings.days_before_expiration,
        expiring_certificates_count=len(expiring),
    )
    
    html_body = _build_html_email_body_outlook_enterprise(
        body_text=body,
        certificates=expiring,
        today=today,
        days_before_expiration=settings.days_before_expiration,
    )

    attachment_name = None
    attachment_csv = None
    if settings.attachment_file_name_template:
        attachment_name = _render_template(
            settings.attachment_file_name_template,
            process_date=today,
            days_before_expiration=settings.days_before_expiration,
            expiring_certificates_count=len(expiring),
        )
        attachment_csv = _build_csv(expiring)

    _send_email(
        settings=settings,
        subject=subject,
        body=body,
        attachment_name=attachment_name,
        attachment_csv=attachment_csv,
        html_body=html_body
    )

    logs_service.create_log(
        session=session,
        action_type="send_notification",
        modified_by="scheduler",
        details=[
            {
                "uid": 1,
                "entity_domain": "notification",
                "entity_id": "scheduled",
                "transaction_description": "Sent scheduled notification.",
                "changes": {
                    "before": None,
                    "after": {
                        "expiring_certificates_count": len(expiring),
                    },
                },
            }
        ],
    )


def send_now(session, modified_by: str) -> None:
    run_scheduled_notifications(session)
    logs_service.create_log(
        session=session,
        action_type="send_notification",
        modified_by=modified_by,
        details=[
            {
                "uid": 1,
                "entity_domain": "notification",
                "entity_id": "manual",
                "transaction_description": "Sent notification manually.",
                "changes": None,
            }
        ],
    )


def _parse_time(value: str) -> time:
    if not _TIME_PATTERN.match(value):
        raise NotificationError("send_time must follow HH:MM.", field="send_time")
    hour, minute = value.split(":")
    return time(hour=int(hour), minute=int(minute))


def _render_template(
    template: str,
    process_date: date,
    days_before_expiration: int,
    expiring_certificates_count: int,
):
    return template.format(
        process_date=process_date.isoformat(),
        days_before_expiration=days_before_expiration,
        expiring_certificates_count=expiring_certificates_count,
    )


def _build_csv(certificates) -> str:
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(
        [
            "certificate",
            "security_token_value",
            "used_by",
            "environment",
            "expiration_date",
        ]
    )
    for cert in certificates:
        writer.writerow(
            [
                cert.certificate,
                cert.security_token_value or "",
                cert.used_by or "",
                cert.environment or "",
                cert.expiration_date.isoformat(),
            ]
        )
    return output.getvalue()

def _send_email(
    settings: NotificationSettings,
    subject: str,
    body: str,
    attachment_name: str | None,
    attachment_csv: str | None,
    html_body: str | None = None,
):
    app_settings = get_app_settings()
    if not app_settings.smtp_host or not app_settings.smtp_port:
        raise NotificationError("SMTP configuration is missing.")

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = formataddr(("CertGuard - Notification", settings.from_email)) #settings.from_email
    message["To"] = ", ".join(settings.recipient_emails)
    
    message.set_content(body)
    
    if html_body:
        message.add_alternative(html_body, subtype="html")

    if attachment_name and attachment_csv:
        message.add_attachment(
            attachment_csv.encode("utf-8"),
            maintype="text",
            subtype="csv",
            filename=attachment_name,
        )

    with smtplib.SMTP(app_settings.smtp_host, app_settings.smtp_port) as smtp:
        if app_settings.smtp_use_tls:
            smtp.starttls()
        if app_settings.smtp_username and app_settings.smtp_password:
            smtp.login(app_settings.smtp_username, app_settings.smtp_password)
        smtp.send_message(message)

def _build_html_email_body_pretty(
    body_text: str,
    certificates,
    today: date,
    days_before_expiration: int,
) -> str:
    rows = []

    body_html = _text_to_html_paragraphs(body_text)
    for cert in certificates:
        days_left = (cert.expiration_date - today).days
        rows.append(
            f"""
            <tr>
                <td style="padding:10px; border:1px solid #d9e2f2;">{html.escape(cert.certificate or "")}</td>
                <td style="padding:10px; border:1px solid #d9e2f2;">{html.escape(cert.used_by or "")}</td>
                <td style="padding:10px; border:1px solid #d9e2f2;">{html.escape(cert.environment or "")}</td>
                <td style="padding:10px; border:1px solid #d9e2f2;">{cert.expiration_date.isoformat()}</td>
                <td style="padding:10px; border:1px solid #d9e2f2; text-align:center;">{days_left}</td>
            </tr>
            """
        )

    rows_html = "".join(rows) if rows else """
        <tr>
            <td colspan="5" style="padding:12px; border:1px solid #d9e2f2; text-align:center;">
                No certificates are currently expiring within the configured timeframe.
            </td>
        </tr>
    """

    return f"""
    <html>
    <body style="margin:0; padding:0; background-color:#f4f6f8; font-family:Arial, Helvetica, sans-serif; color:#1f2937;">
        <div style="max-width:900px; margin:30px auto; background:#ffffff; border:1px solid #e5e7eb; border-radius:10px; overflow:hidden;">
            
            <div style="background:#1f4e79; color:white; padding:20px 30px;">
                <h2 style="margin:0; font-size:24px;">CertGuard Notification</h2>
                <p style="margin:8px 0 0; font-size:14px;">
                    Certificates expiring within the next {days_before_expiration} day(s)
                </p>
            </div>

            <div style="padding:30px;">

                {body_html}                

                <div style="background:#f8fafc; border-left:4px solid #1f4e79; padding:16px; margin:20px 0; border-radius:6px;">
                    <p style="margin:0 0 8px;"><strong>Notification date:</strong> {today.isoformat()}</p>
                    <p style="margin:0;"><strong>Action:</strong> Please review and renew the certificates before expiration.</p>
                </div>

                <h3 style="margin:30px 0 12px; color:#1f4e79;">Certificate Details</h3>

                <table style="width:100%; border-collapse:collapse; font-size:14px;">
                    <thead>
                        <tr style="background:#eaf2f8;">
                            <th style="padding:10px; border:1px solid #d9e2f2; text-align:left;">Certificate</th>
                            <th style="padding:10px; border:1px solid #d9e2f2; text-align:left;">Used By</th>
                            <th style="padding:10px; border:1px solid #d9e2f2; text-align:left;">Environment</th>
                            <th style="padding:10px; border:1px solid #d9e2f2; text-align:left;">Expiration Date</th>
                            <th style="padding:10px; border:1px solid #d9e2f2; text-align:center;">Days Left</th>
                        </tr>
                    </thead>
                    <tbody>
                        {rows_html}
                    </tbody>
                </table>

                <div style="margin-top:24px; padding:16px; background:#fff7ed; border:1px solid #fed7aa; border-radius:6px;">
                    <strong>Action Required:</strong><br>
                    Please ensure that all certificates are renewed before their expiration date.<br>
                    If you have any questions, contact your system administrator.
                </div>

                <p style="margin-top:30px;">
                    Best regards,<br>
                    <strong>CertGuard Notification System</strong>
                </p>
            </div>
        </div>
    </body>
    </html>
    """
    
def _text_to_html_paragraphs(text: str) -> str:
    lines = [line.strip() for line in text.splitlines()]
    paragraphs = [line for line in lines if line]

    return "".join(
        f'<p style="margin:0 0 16px; line-height:1.6;">{html.escape(paragraph)}</p>'
        for paragraph in paragraphs
    )
    
def _build_html_email_body_outlook_enterprise(
    body_text: str,
    certificates,
    today: date,
    days_before_expiration: int,
) -> str:
    body_blocks = _text_to_html_blocks(body_text)

    rows = []
    for cert in certificates:
        days_left = (cert.expiration_date - today).days
        
        if days_left <= 3:
            bg_color = "#fdecea"
            text_color = "#b91c1c"
        elif days_left <= 7:
            bg_color = "#fff4e5"
            text_color = "#b45309"
        else:
            bg_color = "#f3f4f6"
            text_color = "#374151"
            
        rows.append(
            f"""
            <tr>
                <td style="padding: 12px; border: 1px solid #d6dde8; font-family: Arial, Helvetica, sans-serif; font-size: 15px; color: #1f2937;">
                    {html.escape(cert.certificate or "")}
                </td>
                <td style="padding: 12px; border: 1px solid #d6dde8; font-family: Arial, Helvetica, sans-serif; font-size: 15px; color: #1f2937;">
                    {html.escape(cert.used_by or "")}
                </td>
                <td style="padding: 12px; border: 1px solid #d6dde8; font-family: Arial, Helvetica, sans-serif; font-size: 15px; color: #1f2937;">
                    {html.escape(cert.environment or "")}
                </td>
                <td style="padding: 12px; border: 1px solid #d6dde8; font-family: Arial, Helvetica, sans-serif; font-size: 15px; color: #1f2937;">
                    {cert.expiration_date.isoformat()}
                </td>
                <td align="center" style="padding: 12px; border: 1px solid #d6dde8; font-family: Arial, Helvetica, sans-serif; font-size: 15px; background-color:{bg_color}; color:{text_color}; font-weight:bold;">
                    {days_left}
                </td>
            </tr>
            """
        )

    if not rows:
        rows_html = """
        <tr>
            <td colspan="5" align="center" style="padding: 14px; border: 1px solid #d6dde8; font-family: Arial, Helvetica, sans-serif; font-size: 15px; color: #1f2937;">
                No certificates are currently expiring within the configured timeframe.
            </td>
        </tr>
        """
    else:
        rows_html = "".join(rows)

    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta http-equiv="Content-Type" content="text/html; charset=utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>CertGuard Notification</title>
    </head>
    <body style="margin:0; padding:0;">
        <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%" style="background-color:#eef2f7; margin:0; padding:24px 0;">
            <tr>
                <td align="center">

                    <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="900" style="width:900px; max-width:900px; background-color:#ffffff; border-collapse:collapse;">
                        
                        <tr>
                            <td style="background-color:#2f5688; padding:28px 32px;">
                                <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%">
                                    <tr>
                                        <td style="font-family: Arial, Helvetica, sans-serif; font-size: 24px; line-height: 30px; font-weight: bold; color: #ffffff;">
                                            CertGuard Notification
                                        </td>
                                    </tr>
                                    <tr>
                                        <td style="padding-top:8px; font-family: Arial, Helvetica, sans-serif; font-size: 16px; line-height: 22px; color: #dbe7f5;">
                                            Certificates expiring within the next {days_before_expiration} day(s)
                                        </td>
                                    </tr>
                                </table>
                            </td>
                        </tr>

                        {body_blocks}

                        <tr>
                            <td style="padding: 6px 32px 22px 32px;">
                                <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%" style="background-color:#f4f7fb; border-left:4px solid #2f5688;">
                                    <tr>
                                        <td style="padding:16px 18px; font-family: Arial, Helvetica, sans-serif; font-size: 16px; line-height: 24px; color: #1f2937;">
                                            <strong>Notification date:</strong> {today.isoformat()}<br>
                                            <strong>Action:</strong> Please review and renew the certificates before expiration.
                                        </td>
                                    </tr>
                                </table>
                            </td>
                        </tr>

                        <tr>
                            <td style="padding: 4px 32px 14px 32px; font-family: Arial, Helvetica, sans-serif; font-size: 18px; line-height: 24px; font-weight: bold; color: #2f5688;">
                                Certificate Details
                            </td>
                        </tr>

                        <tr>
                            <td style="padding: 0 32px 26px 32px;">
                                <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="800" style="border-collapse:collapse;">
                                    <tr style="background-color:#e8eef5;">
                                        <td style="padding: 12px; border: 1px solid #d6dde8; font-family: Arial, Helvetica, sans-serif; font-size: 15px; font-weight: bold; color: #1f2937;">
                                            Certificate
                                        </td>
                                        <td style="padding: 12px; border: 1px solid #d6dde8; font-family: Arial, Helvetica, sans-serif; font-size: 15px; font-weight: bold; color: #1f2937;">
                                            Used By
                                        </td>
                                        <td style="padding: 12px; border: 1px solid #d6dde8; font-family: Arial, Helvetica, sans-serif; font-size: 15px; font-weight: bold; color: #1f2937;">
                                            Environment
                                        </td>
                                        <td style="padding: 12px; border: 1px solid #d6dde8; font-family: Arial, Helvetica, sans-serif; font-size: 15px; font-weight: bold; color: #1f2937;">
                                            Expiration Date
                                        </td>
                                        <td align="center" style="padding: 12px; border: 1px solid #d6dde8; font-family: Arial, Helvetica, sans-serif; font-size: 15px; font-weight: bold; color: #1f2937;">
                                            Days Left
                                        </td>
                                    </tr>
                                    {rows_html}
                                </table>
                            </td>
                        </tr>

                        <tr>
                            <td style="padding: 0 32px 28px 32px;">
                                <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%" style="background-color:#fbf7f1; border:1px solid #ecd3a7;">
                                    <tr>
                                        <td style="padding:16px 18px; font-family: Arial, Helvetica, sans-serif; font-size: 16px; line-height: 24px; color: #1f2937;">
                                            <strong>Action Required:</strong><br>
                                            Please ensure that all certificates are renewed before their expiration date.<br>
                                            If you have any questions, contact your system administrator.
                                        </td>
                                    </tr>
                                </table>
                            </td>
                        </tr>

                        <tr>
                            <td style="padding: 0 32px 34px 32px; font-family: Arial, Helvetica, sans-serif; font-size: 16px; line-height: 24px; color: #1f2937;">
                                Best regards,<br>
                                <strong>CertGuard Notification System</strong>
                            </td>
                        </tr>

                    </table>

                </td>
            </tr>
        </table>
    </body>
    </html>
    """
    
def _text_to_html_blocks(text: str) -> str:
    paragraphs = [line.strip() for line in text.splitlines() if line.strip()]

    blocks = []
    for paragraph in paragraphs:
        blocks.append(
            f"""
            <tr>
                <td style="padding: 0 32px 18px 32px; font-family: Arial, Helvetica, sans-serif; font-size: 16px; line-height: 24px; color: #1f2937;">
                    {html.escape(paragraph)}
                </td>
            </tr>
            """
        )
    return "".join(blocks)
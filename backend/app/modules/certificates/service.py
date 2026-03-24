from datetime import date
from io import BytesIO

from sqlalchemy.orm import Session

from . import repository
from .models import Certificate
from ..logs import service as logs_service
import pandas as pd
from openpyxl import load_workbook

from .schemas import (
    ConfirmCertificatesImportData,
    ConfirmCertificatesImportRequest,
    CreateCertificateRequest,
    ImportCertificatesPreviewData,
    ImportPreviewItemResponse,
    ImportRowErrorResponse,
    UpdateCertificateRequest,
)


class CertificateError(Exception):
    def __init__(self, message: str, field: str | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.field = field


def _trim_text(value: str | None) -> str | None:
    if value is None:
        return None
    trimmed = value.strip()
    return trimmed if trimmed else None


def create_certificate(
    payload: CreateCertificateRequest, session: Session, modified_by: str
) -> Certificate:
    if repository.get_certificate_by_name(session, payload.certificate.strip()):
        raise CertificateError("Certificate already exists.", field="certificate")

    certificate = Certificate(
        certificate=payload.certificate.strip(),
        security_token_value=_trim_text(payload.security_token_value),
        used_by=_trim_text(payload.used_by),
        environment=_trim_text(payload.environment),
        expiration_date=payload.expiration_date,
    )
    created = repository.create_certificate(session, certificate)
    logs_service.create_log(
        session=session,
        action_type="create_certificate",
        modified_by=modified_by,
        details=[
            {
                "uid": 1,
                "entity_domain": "certificate",
                "entity_id": str(created.id),
                "transaction_description": "Created certificate.",
                "changes": {
                    "before": None,
                    "after": {
                        "certificate": created.certificate,
                        "security_token_value": created.security_token_value,
                        "used_by": created.used_by,
                        "environment": created.environment,
                        "expiration_date": created.expiration_date.isoformat(),
                    },
                },
            }
        ],
    )
    return created


def list_certificates(
    session: Session,
    search: str | None,
    environment: str | None,
    expiring_within_days: int | None,
) -> list[Certificate]:
    return repository.list_certificates(session, search, environment, expiring_within_days)


def get_certificate(certificate_id: int, session: Session) -> Certificate:
    certificate = repository.get_certificate_by_id(session, certificate_id)
    if certificate is None:
        raise CertificateError("Certificate not found.", field="certificate_id")
    return certificate


def update_certificate(
    certificate_id: int,
    payload: UpdateCertificateRequest,
    session: Session,
    modified_by: str,
) -> Certificate:
    certificate = repository.get_certificate_by_id(session, certificate_id)
    if certificate is None:
        raise CertificateError("Certificate not found.", field="certificate_id")

    new_name = payload.certificate.strip()
    if new_name != certificate.certificate:
        if repository.get_certificate_by_name(session, new_name):
            raise CertificateError("Certificate already exists.", field="certificate")

    before = {
        "certificate": certificate.certificate,
        "security_token_value": certificate.security_token_value,
        "used_by": certificate.used_by,
        "environment": certificate.environment,
        "expiration_date": certificate.expiration_date.isoformat(),
    }

    certificate.certificate = new_name
    certificate.security_token_value = _trim_text(payload.security_token_value)
    certificate.used_by = _trim_text(payload.used_by)
    certificate.environment = _trim_text(payload.environment)
    certificate.expiration_date = payload.expiration_date

    updated = repository.update_certificate(session, certificate)
    logs_service.create_log(
        session=session,
        action_type="update_certificate",
        modified_by=modified_by,
        details=[
            {
                "uid": 1,
                "entity_domain": "certificate",
                "entity_id": str(updated.id),
                "transaction_description": "Updated certificate.",
                "changes": {
                    "before": before,
                    "after": {
                        "certificate": updated.certificate,
                        "security_token_value": updated.security_token_value,
                        "used_by": updated.used_by,
                        "environment": updated.environment,
                        "expiration_date": updated.expiration_date.isoformat(),
                    },
                },
            }
        ],
    )
    return updated


def delete_certificate(certificate_id: int, session: Session, modified_by: str) -> None:
    certificate = repository.get_certificate_by_id(session, certificate_id)
    if certificate is None:
        raise CertificateError("Certificate not found.", field="certificate_id")

    repository.soft_delete_certificate(session, certificate)
    logs_service.create_log(
        session=session,
        action_type="delete_certificate",
        modified_by=modified_by,
        details=[
            {
                "uid": 1,
                "entity_domain": "certificate",
                "entity_id": str(certificate.id),
                "transaction_description": "Deleted certificate.",
                "changes": None,
            }
        ],
    )


_EXPECTED_COLUMNS = {
    "certificate": "certificate",
    "security token value (serial number)": "security_token_value",
    "used by": "used_by",
    "environments": "environment",
    "expiration date": "expiration_date",
}


def _normalize_columns(columns: list[str]) -> dict[str, str]:
    mapping: dict[str, str] = {}
    for name in columns:
        key = name.strip().lower()
        if key in _EXPECTED_COLUMNS:
            mapping[name] = _EXPECTED_COLUMNS[key]
    return mapping


def _normalize_cell(value) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        return _trim_text(value)
    return str(value).strip() or None


def _parse_date(value) -> date | None:
    if value is None or value == "":
        return None
    if isinstance(value, date):
        return value
    parsed = pd.to_datetime(value, errors="coerce")
    if pd.isna(parsed):
        return None
    return parsed.date()


def _validate_row(row: dict, row_number: int) -> tuple[dict | None, ImportRowErrorResponse | None]:
    certificate_value = _normalize_cell(row.get("certificate"))
    expiration_date_value = _parse_date(row.get("expiration_date"))

    if not certificate_value:
        return None, ImportRowErrorResponse(
            row_number=row_number, detail="Certificate is required."
        )
    if not expiration_date_value:
        return None, ImportRowErrorResponse(
            row_number=row_number, detail="Expiration date is required."
        )

    cleaned = {
        "certificate": certificate_value,
        "security_token_value": _normalize_cell(row.get("security_token_value")),
        "used_by": _normalize_cell(row.get("used_by")),
        "environment": _normalize_cell(row.get("environment")),
        "expiration_date": expiration_date_value,
    }
    return cleaned, None


def _load_dataframe(file_bytes: bytes) -> pd.DataFrame:
    workbook = load_workbook(filename=BytesIO(file_bytes), data_only=True)
    sheet = workbook.active
    data = list(sheet.values)
    if not data:
        return pd.DataFrame()
    header = [str(cell).strip() if cell is not None else "" for cell in data[0]]
    rows = data[1:]
    return pd.DataFrame(rows, columns=header)


def preview_import(file_bytes: bytes, session: Session) -> ImportCertificatesPreviewData:
    dataframe = _load_dataframe(file_bytes)
    if dataframe.empty:
        return ImportCertificatesPreviewData(
            total_rows=0,
            valid_rows=0,
            insert_count=0,
            update_count=0,
            skipped_count=0,
            errors=[],
            preview_items=[],
        )

    column_mapping = _normalize_columns(list(dataframe.columns))
    dataframe = dataframe.rename(columns=column_mapping)

    for required in _EXPECTED_COLUMNS.values():
        if required not in dataframe.columns:
            raise CertificateError(f"Missing required column: {required}.", field=required)

    errors: list[ImportRowErrorResponse] = []
    preview_items: list[ImportPreviewItemResponse] = []
    seen_certificates: set[str] = set()

    total_rows = len(dataframe.index)
    valid_rows = 0
    insert_count = 0
    update_count = 0
    skipped_count = 0

    for idx, row in dataframe.iterrows():
        row_number = idx + 2
        row_dict = row.to_dict()
        if all(value is None or str(value).strip() == "" for value in row_dict.values()):
            skipped_count += 1
            continue

        cleaned, error = _validate_row(row_dict, row_number)
        if error:
            errors.append(error)
            skipped_count += 1
            continue

        assert cleaned is not None
        if cleaned["certificate"] in seen_certificates:
            skipped_count += 1
            continue
        seen_certificates.add(cleaned["certificate"])

        exists = repository.get_certificate_by_name(session, cleaned["certificate"])
        action = "update" if exists else "insert"
        if action == "update":
            update_count += 1
        else:
            insert_count += 1

        valid_rows += 1
        preview_items.append(
            ImportPreviewItemResponse(
                row_number=row_number,
                certificate=cleaned["certificate"],
                security_token_value=cleaned["security_token_value"],
                used_by=cleaned["used_by"],
                environment=cleaned["environment"],
                expiration_date=cleaned["expiration_date"],
                action=action,
            )
        )

    return ImportCertificatesPreviewData(
        total_rows=total_rows,
        valid_rows=valid_rows,
        insert_count=insert_count,
        update_count=update_count,
        skipped_count=skipped_count,
        errors=errors,
        preview_items=preview_items,
    )


def confirm_import(
    payload: ConfirmCertificatesImportRequest,
    session: Session,
    modified_by: str,
) -> ConfirmCertificatesImportData:
    insert_count = 0
    update_count = 0
    skipped_count = 0
    errors: list[ImportRowErrorResponse] = []

    for idx, item in enumerate(payload.items, start=1):
        cleaned, error = _validate_row(item.dict(), row_number=idx)
        if error:
            errors.append(error)
            skipped_count += 1
            continue

        assert cleaned is not None
        existing = repository.get_certificate_by_name(session, cleaned["certificate"])
        if existing:
            existing.security_token_value = cleaned["security_token_value"]
            existing.used_by = cleaned["used_by"]
            existing.environment = cleaned["environment"]
            existing.expiration_date = cleaned["expiration_date"]
            repository.update_certificate(session, existing)
            update_count += 1
        else:
            certificate = Certificate(
                certificate=cleaned["certificate"],
                security_token_value=cleaned["security_token_value"],
                used_by=cleaned["used_by"],
                environment=cleaned["environment"],
                expiration_date=cleaned["expiration_date"],
            )
            repository.create_certificate(session, certificate)
            insert_count += 1

    result = ConfirmCertificatesImportData(
        insert_count=insert_count,
        update_count=update_count,
        skipped_count=skipped_count,
        errors=errors,
    )

    logs_service.create_log(
        session=session,
        action_type="import_certificates",
        modified_by=modified_by,
        details=[
            {
                "uid": 1,
                "entity_domain": "import",
                "entity_id": "certificates",
                "transaction_description": "Imported certificates.",
                "changes": {
                    "before": None,
                    "after": {
                        "insert_count": result.insert_count,
                        "update_count": result.update_count,
                        "skipped_count": result.skipped_count,
                    },
                },
            }
        ],
    )

    return result

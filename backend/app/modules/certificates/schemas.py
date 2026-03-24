from datetime import date, datetime
from typing import List, Literal, Optional

from pydantic import BaseModel


class ErrorItem(BaseModel):
    field: Optional[str]
    detail: str


class StandardErrorResponse(BaseModel):
    success: bool = False
    message: str
    errors: List[ErrorItem]


class CreateCertificateRequest(BaseModel):
    certificate: str
    security_token_value: Optional[str] = None
    used_by: Optional[str] = None
    environment: Optional[str] = None
    expiration_date: date


class UpdateCertificateRequest(BaseModel):
    certificate: str
    security_token_value: Optional[str] = None
    used_by: Optional[str] = None
    environment: Optional[str] = None
    expiration_date: date


class CertificateResponse(BaseModel):
    id: int
    certificate: str
    security_token_value: Optional[str]
    used_by: Optional[str]
    environment: Optional[str]
    expiration_date: date
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True


class CertificateSuccessResponse(BaseModel):
    success: bool = True
    message: str
    data: CertificateResponse


class CertificatesListResponse(BaseModel):
    success: bool = True
    message: str
    data: List[CertificateResponse]


class CertificateDeleteResponse(BaseModel):
    success: bool = True
    message: str
    data: None = None


class ImportRowErrorResponse(BaseModel):
    row_number: int
    detail: str


class ImportPreviewItemResponse(BaseModel):
    row_number: int
    certificate: str
    security_token_value: Optional[str]
    used_by: Optional[str]
    environment: Optional[str]
    expiration_date: date
    action: Literal["insert", "update"]


class ImportCertificatesPreviewData(BaseModel):
    total_rows: int
    valid_rows: int
    insert_count: int
    update_count: int
    skipped_count: int
    errors: List[ImportRowErrorResponse]
    preview_items: List[ImportPreviewItemResponse]


class ImportCertificatesPreviewResponse(BaseModel):
    success: bool = True
    message: str
    data: ImportCertificatesPreviewData


class ConfirmCertificatesImportItem(BaseModel):
    certificate: str
    security_token_value: Optional[str] = None
    used_by: Optional[str] = None
    environment: Optional[str] = None
    expiration_date: date


class ConfirmCertificatesImportRequest(BaseModel):
    items: List[ConfirmCertificatesImportItem]


class ConfirmCertificatesImportData(BaseModel):
    insert_count: int
    update_count: int
    skipped_count: int
    errors: List[ImportRowErrorResponse]


class ConfirmCertificatesImportResponse(BaseModel):
    success: bool = True
    message: str
    data: ConfirmCertificatesImportData

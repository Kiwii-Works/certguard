from fastapi import APIRouter, Depends, File, UploadFile, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from ...core.auth import get_current_user, require_admin
from ...core.database import get_session
from . import service
from .schemas import (
    CertificateResponse,
    CertificateDeleteResponse,
    CertificateSuccessResponse,
    CertificatesListResponse,
    ConfirmCertificatesImportRequest,
    ConfirmCertificatesImportResponse,
    ErrorItem,
    ImportCertificatesPreviewResponse,
    StandardErrorResponse,
    UpdateCertificateRequest,
    CreateCertificateRequest,
)

router = APIRouter(prefix="/api/v1/certificates", tags=["certificates"])


def _error_response(message: str, field: str | None, status_code: int):
    error = StandardErrorResponse(
        success=False,
        message=message,
        errors=[ErrorItem(field=field, detail=message)],
    )
    return JSONResponse(status_code=status_code, content=error.dict())


@router.post(
    "",
    response_model=CertificateSuccessResponse,
    responses={400: {"model": StandardErrorResponse}},
    dependencies=[Depends(require_admin)],
)
def create_certificate(
    payload: CreateCertificateRequest,
    session: Session = Depends(get_session),
    current_user=Depends(require_admin),
) -> CertificateSuccessResponse:
    try:
        certificate = service.create_certificate(
            payload, session, modified_by=current_user.username
        )
    except service.CertificateError as exc:
        return _error_response(exc.message, exc.field, status.HTTP_400_BAD_REQUEST)

    return CertificateSuccessResponse(
        success=True,
        message="Certificate created successfully.",
        data=CertificateResponse.model_validate(certificate, from_attributes=True),
    )


@router.get("", response_model=CertificatesListResponse, dependencies=[Depends(get_current_user)])
def list_certificates(
    search: str | None = None,
    environment: str | None = None,
    expiring_within_days: int | None = None,
    session: Session = Depends(get_session),
) -> CertificatesListResponse:
    certificates = service.list_certificates(session, search, environment, expiring_within_days)
    serialized_certificates = [
        CertificateResponse.model_validate(certificate, from_attributes=True)
        for certificate in certificates
    ]
    return CertificatesListResponse(
        success=True,
        message="Certificates retrieved successfully.",
        data=serialized_certificates,
    )


@router.get(
    "/{certificate_id}",
    response_model=CertificateSuccessResponse,
    responses={404: {"model": StandardErrorResponse}},
    dependencies=[Depends(get_current_user)],
)
def get_certificate(certificate_id: int, session: Session = Depends(get_session)):
    try:
        certificate = service.get_certificate(certificate_id, session)
    except service.CertificateError as exc:
        return _error_response(exc.message, exc.field, status.HTTP_404_NOT_FOUND)

    return CertificateSuccessResponse(
        success=True,
        message="Certificate retrieved successfully.",
        data=CertificateResponse.model_validate(certificate, from_attributes=True),
    )


@router.put(
    "/{certificate_id}",
    response_model=CertificateSuccessResponse,
    responses={400: {"model": StandardErrorResponse}, 404: {"model": StandardErrorResponse}},
    dependencies=[Depends(require_admin)],
)
def update_certificate(
    certificate_id: int,
    payload: UpdateCertificateRequest,
    session: Session = Depends(get_session),
    current_user=Depends(require_admin),
):
    try:
        certificate = service.update_certificate(
            certificate_id, payload, session, modified_by=current_user.username
        )
    except service.CertificateError as exc:
        status_code = (
            status.HTTP_404_NOT_FOUND
            if exc.field == "certificate_id"
            else status.HTTP_400_BAD_REQUEST
        )
        return _error_response(exc.message, exc.field, status_code)

    return CertificateSuccessResponse(
        success=True,
        message="Certificate updated successfully.",
        data=CertificateResponse.model_validate(certificate, from_attributes=True),
    )


@router.delete(
    "/{certificate_id}",
    response_model=CertificateDeleteResponse,
    responses={404: {"model": StandardErrorResponse}},
    dependencies=[Depends(require_admin)],
)
def delete_certificate(
    certificate_id: int,
    session: Session = Depends(get_session),
    current_user=Depends(require_admin),
) -> CertificateDeleteResponse:
    try:
        service.delete_certificate(certificate_id, session, modified_by=current_user.username)
    except service.CertificateError as exc:
        return _error_response(exc.message, exc.field, status.HTTP_404_NOT_FOUND)

    return CertificateDeleteResponse(
        success=True,
        message="Certificate deleted successfully.",
        data=None,
    )


@router.post(
    "/import/preview",
    response_model=ImportCertificatesPreviewResponse,
    responses={400: {"model": StandardErrorResponse}},
    dependencies=[Depends(require_admin)],
)
def import_preview(
    file: UploadFile = File(...), session: Session = Depends(get_session)
):
    try:
        content = file.file.read()
        preview = service.preview_import(content, session)
    except service.CertificateError as exc:
        return _error_response(exc.message, exc.field, status.HTTP_400_BAD_REQUEST)
    except NotImplementedError as exc:
        return _error_response(str(exc), field=None, status_code=status.HTTP_400_BAD_REQUEST)

    return ImportCertificatesPreviewResponse(
        success=True,
        message="Import preview generated successfully.",
        data=preview,
    )


@router.post(
    "/import/confirm",
    response_model=ConfirmCertificatesImportResponse,
    responses={400: {"model": StandardErrorResponse}},
    dependencies=[Depends(require_admin)],
)
def import_confirm(
    payload: ConfirmCertificatesImportRequest,
    session: Session = Depends(get_session),
    current_user=Depends(require_admin),
):
    try:
        result = service.confirm_import(
            payload, session, modified_by=current_user.username
        )
    except service.CertificateError as exc:
        return _error_response(exc.message, exc.field, status.HTTP_400_BAD_REQUEST)
    except NotImplementedError as exc:
        return _error_response(str(exc), field=None, status_code=status.HTTP_400_BAD_REQUEST)

    return ConfirmCertificatesImportResponse(
        success=True,
        message="Certificates imported successfully.",
        data=result,
    )

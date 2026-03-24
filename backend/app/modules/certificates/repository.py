from datetime import date

from sqlalchemy.orm import Session

from .models import Certificate


def list_certificates(
    session: Session,
    search: str | None,
    environment: str | None,
    expiring_within_days: int | None,
) -> list[Certificate]:
    query = session.query(Certificate).filter(Certificate.is_deleted.is_(False))
    if search:
        query = query.filter(Certificate.certificate.ilike(f"%{search}%"))
    if environment:
        query = query.filter(Certificate.environment == environment)
    if expiring_within_days is not None:
        from datetime import timedelta

        upper = date.today() + timedelta(days=expiring_within_days)
        query = query.filter(Certificate.expiration_date <= upper)

    return query.all()


def count_certificates(session: Session) -> int:
    return session.query(Certificate).filter(Certificate.is_deleted.is_(False)).count()


def count_expiring_soon(session: Session, cutoff_date: date) -> int:
    return (
        session.query(Certificate)
        .filter(
            Certificate.is_deleted.is_(False),
            Certificate.expiration_date <= cutoff_date,
        )
        .count()
    )


def get_certificate_by_id(session: Session, certificate_id: int) -> Certificate | None:
    return (
        session.query(Certificate)
        .filter(Certificate.id == certificate_id, Certificate.is_deleted.is_(False))
        .one_or_none()
    )


def get_certificate_by_name(session: Session, certificate_name: str) -> Certificate | None:
    return (
        session.query(Certificate)
        .filter(
            Certificate.certificate == certificate_name,
            Certificate.is_deleted.is_(False),
        )
        .one_or_none()
    )


def create_certificate(session: Session, certificate: Certificate) -> Certificate:
    session.add(certificate)
    session.commit()
    session.refresh(certificate)
    return certificate


def update_certificate(session: Session, certificate: Certificate) -> Certificate:
    session.add(certificate)
    session.commit()
    session.refresh(certificate)
    return certificate


def soft_delete_certificate(session: Session, certificate: Certificate) -> Certificate:
    certificate.is_deleted = True
    session.add(certificate)
    session.commit()
    session.refresh(certificate)
    return certificate

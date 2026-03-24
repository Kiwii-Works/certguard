from sqlalchemy.orm import Session

from .models import User


def count_users(session: Session) -> int:
    return session.query(User).filter(User.is_deleted.is_(False)).count()


def count_active_users(session: Session) -> int:
    return (
        session.query(User)
        .filter(User.is_deleted.is_(False), User.is_active.is_(True))
        .count()
    )


def list_users(session: Session) -> list[User]:
    return session.query(User).filter(User.is_deleted.is_(False)).all()


def get_user_by_id(session: Session, user_id: str) -> User | None:
    return (
        session.query(User)
        .filter(User.id == user_id, User.is_deleted.is_(False))
        .one_or_none()
    )


def get_user_by_username(session: Session, username: str) -> User | None:
    return (
        session.query(User)
        .filter(User.username == username, User.is_deleted.is_(False))
        .one_or_none()
    )


def get_user_by_email(session: Session, email: str) -> User | None:
    return (
        session.query(User)
        .filter(User.email == email, User.is_deleted.is_(False))
        .one_or_none()
    )


def create_user(
    session: Session,
    username: str,
    email: str,
    password_hash: str,
    role: str,
    is_active: bool,
) -> User:
    user = User(
        username=username,
        email=email,
        password_hash=password_hash,
        role=role,
        is_active=is_active,
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


def update_user(session: Session, user: User) -> User:
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


def soft_delete_user(session: Session, user: User) -> User:
    user.is_deleted = True
    session.add(user)
    session.commit()
    session.refresh(user)
    return user

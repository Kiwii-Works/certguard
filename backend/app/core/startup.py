from .config import get_settings
from .database import SessionLocal, create_all
from .security import hash_password
from ..modules.users.repository import count_users, create_user


def initialize_app() -> None:
    get_settings()
    create_all()

    session = SessionLocal()
    try:
        if count_users(session) == 0:
            create_user(
                session=session,
                username="admin",
                email="admin@certguard.local",
                password_hash=hash_password("Admin123!"),
                role="admin",
                is_active=True,
            )
    finally:
        session.close()

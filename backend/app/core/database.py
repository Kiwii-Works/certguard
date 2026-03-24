from functools import lru_cache

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from .config import get_settings

Base = declarative_base()


def _is_sqlite(database_url: str) -> bool:
    return database_url.startswith("sqlite")


@lru_cache
def get_engine():
    settings = get_settings()
    connect_args = {"check_same_thread": False} if _is_sqlite(settings.database_url) else {}
    return create_engine(settings.database_url, connect_args=connect_args)


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=get_engine())


def get_session():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def create_all() -> None:
    Base.metadata.create_all(bind=get_engine())

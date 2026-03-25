import os
from dataclasses import dataclass
from functools import lru_cache
from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    database_url: str
    jwt_secret_key: str
    jwt_algorithm: str
    access_token_expire_seconds: int
    smtp_host: str | None
    smtp_port: int | None
    smtp_username: str | None
    smtp_password: str | None
    smtp_use_tls: bool


@lru_cache
def get_settings() -> Settings:
    database_url = os.getenv("DATABASE_URL", "sqlite:///./certguard.db")
    jwt_secret_key = os.getenv("JWT_SECRET_KEY")
    if not jwt_secret_key:
        raise RuntimeError("JWT_SECRET_KEY is required")

    jwt_algorithm = os.getenv("JWT_ALGORITHM", "HS256")
    access_token_expire_seconds = int(
        os.getenv("ACCESS_TOKEN_EXPIRE_SECONDS", "3600")
    )

    smtp_host = os.getenv("SMTP_HOST")
    smtp_port_raw = os.getenv("SMTP_PORT")
    smtp_port = int(smtp_port_raw) if smtp_port_raw else None
    smtp_username = os.getenv("SMTP_USERNAME")
    smtp_password = os.getenv("SMTP_PASSWORD")
    smtp_use_tls = os.getenv("SMTP_USE_TLS", "true").lower() == "true"

    return Settings(
        database_url=database_url,
        jwt_secret_key=jwt_secret_key,
        jwt_algorithm=jwt_algorithm,
        access_token_expire_seconds=access_token_expire_seconds,
        smtp_host=smtp_host,
        smtp_port=smtp_port,
        smtp_username=smtp_username,
        smtp_password=smtp_password,
        smtp_use_tls=smtp_use_tls,
    )

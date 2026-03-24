from sqlalchemy.orm import Session

from ...core.config import get_settings
from ...core.security import create_access_token, verify_password
from ..logs import service as logs_service
from ..users.repository import get_user_by_username
from .schemas import AuthenticatedUserResponse, LoginRequest, LoginResponseData


class AuthError(Exception):
    def __init__(self, message: str, field: str | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.field = field


def login(payload: LoginRequest, session: Session) -> LoginResponseData:
    user = get_user_by_username(session, payload.username)
    if user is None:
        raise AuthError("Invalid username or password.", field="username")
    if not user.is_active:
        raise AuthError("User is inactive.", field="is_active")
    if not verify_password(payload.password, user.password_hash):
        raise AuthError("Invalid username or password.", field="password")

    settings = get_settings()
    access_token = create_access_token(
        subject=user.id,
        role=user.role,
        expires_in_seconds=settings.access_token_expire_seconds,
    )

    response = LoginResponseData(
        access_token=access_token,
        token_type="bearer",
        expires_in_seconds=settings.access_token_expire_seconds,
        user=AuthenticatedUserResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            role=user.role,
            is_active=user.is_active,
        ),
    )

    logs_service.create_log(
        session=session,
        action_type="login",
        modified_by=user.username,
        details=[
            {
                "uid": 1,
                "entity_domain": "auth",
                "entity_id": user.id,
                "transaction_description": "User logged in.",
                "changes": None,
            }
        ],
    )

    return response


def get_current_user() -> AuthenticatedUserResponse:
    """Placeholder current user lookup until persistence is added."""
    return AuthenticatedUserResponse(
        id=1,
        username="admin",
        email="admin@example.com",
        role="admin",
        is_active=True,
    )


def logout(session: Session, modified_by: str, user_id: str) -> None:
    """Placeholder logout until token revocation is introduced."""
    logs_service.create_log(
        session=session,
        action_type="logout",
        modified_by=modified_by,
        details=[
            {
                "uid": 1,
                "entity_domain": "auth",
                "entity_id": user_id,
                "transaction_description": "User logged out.",
                "changes": None,
            }
        ],
    )
    return None

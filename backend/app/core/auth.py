from typing import Optional

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from pydantic import BaseModel
from sqlalchemy.orm import Session

from .database import get_session
from .security import decode_access_token


class ErrorItem(BaseModel):
    field: Optional[str]
    detail: str


class StandardErrorResponse(BaseModel):
    success: bool = False
    message: str
    errors: list[ErrorItem]


class AuthException(Exception):
    def __init__(self, status_code: int, message: str, field: str | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.message = message
        self.field = field


bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    session: Session = Depends(get_session),
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
):
    from ..modules.users.repository import get_user_by_id

    if credentials is None:
        raise AuthException(401, "Authorization required.")

    try:
        payload = decode_access_token(credentials.credentials)
    except JWTError as exc:
        raise AuthException(401, "Invalid or expired token.") from exc

    user_id = payload.get("sub")
    if not user_id:
        raise AuthException(401, "Invalid token payload.")

    user = get_user_by_id(session, user_id)
    if user is None or user.is_deleted:
        raise AuthException(401, "User not found.", field="user_id")
    if not user.is_active:
        raise AuthException(401, "User is inactive.", field="is_active")

    return user


def require_admin(current_user=Depends(get_current_user)):
    if current_user.role != "admin":
        raise AuthException(403, "Admin access required.", field="role")
    return current_user

from typing import List, Optional

from pydantic import BaseModel


class ErrorItem(BaseModel):
    field: Optional[str]
    detail: str


class StandardErrorResponse(BaseModel):
    success: bool = False
    message: str
    errors: List[ErrorItem]


class LoginRequest(BaseModel):
    username: str
    password: str


class AuthenticatedUserResponse(BaseModel):
    id: str
    username: str
    email: str
    role: str
    is_active: bool

    class Config:
        orm_mode = True


class LoginResponseData(BaseModel):
    access_token: str
    token_type: str
    expires_in_seconds: int
    user: AuthenticatedUserResponse


class LoginResponse(BaseModel):
    success: bool = True
    message: str
    data: LoginResponseData


class CurrentUserResponse(BaseModel):
    success: bool = True
    message: str
    data: AuthenticatedUserResponse


class LogoutResponse(BaseModel):
    success: bool = True
    message: str
    data: None = None

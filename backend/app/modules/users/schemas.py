from datetime import datetime
from typing import List, Literal, Optional

from pydantic import BaseModel


class ErrorItem(BaseModel):
    field: Optional[str]
    detail: str


class StandardErrorResponse(BaseModel):
    success: bool = False
    message: str
    errors: List[ErrorItem]


class CreateUserRequest(BaseModel):
    username: str
    email: str
    password: str
    role: Literal["admin", "user"]
    is_active: bool


class UpdateUserRequest(BaseModel):
    username: str
    email: str
    role: Literal["admin", "user"]
    is_active: bool


class ChangeUserPasswordRequest(BaseModel):
    new_password: str


class UserResponse(BaseModel):
    id: str
    username: str
    email: str
    role: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True


class UserSuccessResponse(BaseModel):
    success: bool = True
    message: str
    data: UserResponse


class UsersListResponse(BaseModel):
    success: bool = True
    message: str
    data: List[UserResponse]


class UserDeleteResponse(BaseModel):
    success: bool = True
    message: str
    data: None = None

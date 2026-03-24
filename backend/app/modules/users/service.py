from sqlalchemy.orm import Session

from ...core.security import hash_password
from ..logs import service as logs_service
from . import repository
from .schemas import ChangeUserPasswordRequest, CreateUserRequest, UpdateUserRequest


class UserError(Exception):
    def __init__(self, message: str, field: str | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.field = field


def create_user(payload: CreateUserRequest, session: Session, modified_by: str):
    if repository.get_user_by_username(session, payload.username):
        raise UserError("Username already exists.", field="username")
    if repository.get_user_by_email(session, payload.email):
        raise UserError("Email already exists.", field="email")

    password_hash = hash_password(payload.password)
    user = repository.create_user(
        session=session,
        username=payload.username,
        email=payload.email,
        password_hash=password_hash,
        role=payload.role,
        is_active=payload.is_active,
    )
    logs_service.create_log(
        session=session,
        action_type="create_user",
        modified_by=modified_by,
        details=[
            {
                "uid": 1,
                "entity_domain": "user",
                "entity_id": user.id,
                "transaction_description": "Created user.",
                "changes": {
                    "before": None,
                    "after": {
                        "username": user.username,
                        "email": user.email,
                        "role": user.role,
                        "is_active": user.is_active,
                    },
                },
            }
        ],
    )
    return user


def list_users(session: Session):
    return repository.list_users(session)


def get_user(user_id: str, session: Session):
    user = repository.get_user_by_id(session, user_id)
    if user is None:
        raise UserError("User not found.", field="user_id")
    return user


def update_user(user_id: str, payload: UpdateUserRequest, session: Session, modified_by: str):
    user = repository.get_user_by_id(session, user_id)
    if user is None:
        raise UserError("User not found.", field="user_id")

    if payload.username != user.username:
        if repository.get_user_by_username(session, payload.username):
            raise UserError("Username already exists.", field="username")
    if payload.email != user.email:
        if repository.get_user_by_email(session, payload.email):
            raise UserError("Email already exists.", field="email")

    before = {
        "username": user.username,
        "email": user.email,
        "role": user.role,
        "is_active": user.is_active,
    }

    user.username = payload.username
    user.email = payload.email
    user.role = payload.role
    user.is_active = payload.is_active

    updated = repository.update_user(session, user)
    logs_service.create_log(
        session=session,
        action_type="update_user",
        modified_by=modified_by,
        details=[
            {
                "uid": 1,
                "entity_domain": "user",
                "entity_id": updated.id,
                "transaction_description": "Updated user.",
                "changes": {"before": before, "after": {
                    "username": updated.username,
                    "email": updated.email,
                    "role": updated.role,
                    "is_active": updated.is_active,
                }},
            }
        ],
    )
    return updated


def change_password(
    user_id: str, payload: ChangeUserPasswordRequest, session: Session, modified_by: str
):
    user = repository.get_user_by_id(session, user_id)
    if user is None:
        raise UserError("User not found.", field="user_id")

    user.password_hash = hash_password(payload.new_password)
    updated = repository.update_user(session, user)
    logs_service.create_log(
        session=session,
        action_type="change_user_password",
        modified_by=modified_by,
        details=[
            {
                "uid": 1,
                "entity_domain": "user",
                "entity_id": updated.id,
                "transaction_description": "Changed user password.",
                "changes": None,
            }
        ],
    )
    return updated


def delete_user(user_id: str, session: Session, modified_by: str) -> None:
    user = repository.get_user_by_id(session, user_id)
    if user is None:
        raise UserError("User not found.", field="user_id")

    repository.soft_delete_user(session, user)
    logs_service.create_log(
        session=session,
        action_type="delete_user",
        modified_by=modified_by,
        details=[
            {
                "uid": 1,
                "entity_domain": "user",
                "entity_id": user.id,
                "transaction_description": "Deleted user.",
                "changes": None,
            }
        ],
    )

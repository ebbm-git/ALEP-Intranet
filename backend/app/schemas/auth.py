from __future__ import annotations

import uuid

from pydantic import BaseModel, ConfigDict, EmailStr

from app.models.user_profile import UserRole


class CurrentUserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: uuid.UUID
    email: EmailStr
    full_name: str | None
    role: UserRole
    accessible_page_ids: list[uuid.UUID] = []


class UserProfileRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: uuid.UUID
    email: EmailStr
    full_name: str | None
    role: UserRole


class UserRoleUpdate(BaseModel):
    role: UserRole


class RolePagePermissionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    role: UserRole
    page_id: uuid.UUID


class PermissionCell(BaseModel):
    role: UserRole
    page_id: uuid.UUID
    has_access: bool

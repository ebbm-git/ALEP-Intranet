from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class UserRole(str, enum.Enum):
    """Application-level roles. Stored in user_profiles.role.

    Capabilities (declarative — actual enforcement is in app.core.permissions):
      admin         : full access; no permission grid lookup; only role that
                      can create new pages, change roles, edit the permission
                      grid, and access the Configurações area.
      editor_chief  : may edit + delete content blocks on pages they have
                      access to. No access to Configurações. No page creation.
      editor_a      : may edit content blocks (incl. insert and restore) on
                      pages they have access to. No deletes.
      editor_b      : same as editor_a — having two parallel "editor" roles
                      is intentional so the permission grid can give different
                      page access to different departments at the same tier.
      viewer        : read-only on pages they have access to.
    """

    admin = "admin"
    editor_chief = "editor_chief"
    editor_a = "editor_a"
    editor_b = "editor_b"
    viewer = "viewer"


# Used in code as a quick "what is the rank?" comparison.
ROLE_RANK: dict[UserRole, int] = {
    UserRole.viewer: 1,
    UserRole.editor_b: 2,
    UserRole.editor_a: 3,
    UserRole.editor_chief: 4,
    UserRole.admin: 5,
}


class UserProfile(Base):
    """Application profile for a Supabase Auth user.

    `user_id` matches the UUID in Supabase's `auth.users` table. We intentionally
    do NOT use a cross-schema foreign key because the `auth` schema is owned by
    Supabase — instead we keep the UUID by value and let the application layer
    enforce existence.
    """

    __tablename__ = "user_profiles"

    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    full_name: Mapped[str | None] = mapped_column(String(255))
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, name="user_role", native_enum=False, length=32),
        nullable=False,
        default=UserRole.viewer,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

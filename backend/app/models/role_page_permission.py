from __future__ import annotations

import uuid

from sqlalchemy import Enum, ForeignKey, PrimaryKeyConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.user_profile import UserRole


class RolePagePermission(Base):
    """Permission grid: presence of a row means `role` has access to `page_id`.

    The four non-admin roles each get their own row per page they can access.
    `admin` is NEVER stored here — admins implicitly have access to every page.
    `viewer` rows mean "may view"; `editor_*` rows mean "may view + the
    capabilities defined by the role".
    """

    __tablename__ = "role_page_permissions"
    __table_args__ = (PrimaryKeyConstraint("role", "page_id"),)

    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, name="user_role", native_enum=False, length=32, create_type=False),
        nullable=False,
    )
    page_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("pages.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

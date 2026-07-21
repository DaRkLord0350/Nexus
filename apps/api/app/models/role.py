from sqlalchemy import Boolean, Column, String, Text, UniqueConstraint
from sqlalchemy.orm import relationship

from app.db import Base
from app.models.base import TimestampMixin, TenantMixin


class Role(Base, TimestampMixin, TenantMixin):
    __tablename__ = "roles"
    __table_args__ = (UniqueConstraint("organization_id", "name", name="uq_organization_role_name"),)

    name = Column(String(128), nullable=False, index=True)
    description = Column(Text, nullable=True)
    built_in = Column(Boolean, default=False, nullable=False)

    permissions = relationship("RolePermission", back_populates="role", cascade="all, delete-orphan")
    user_roles = relationship("UserRole", back_populates="role", cascade="all, delete-orphan")

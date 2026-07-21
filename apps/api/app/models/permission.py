from sqlalchemy import Column, String, Text, UniqueConstraint
from sqlalchemy.orm import relationship

from app.db import Base
from app.models.base import TimestampMixin, TenantMixin


class Permission(Base, TimestampMixin, TenantMixin):
    __tablename__ = "permissions"
    __table_args__ = (UniqueConstraint("organization_id", "code", name="uq_organization_permission_code"),)

    code = Column(String(64), nullable=False, index=True)
    name = Column(String(128), nullable=False)
    description = Column(Text, nullable=True)

    role_permissions = relationship("RolePermission", back_populates="permission", cascade="all, delete-orphan")

from sqlalchemy import Column, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import relationship

from app.db import Base
from app.models.base import TimestampMixin, TenantMixin


class RolePermission(Base, TimestampMixin, TenantMixin):
    __tablename__ = "role_permissions"
    __table_args__ = (UniqueConstraint("role_id", "permission_id", name="uq_role_permission"),)

    role_id = Column(String(36), ForeignKey("roles.id"), nullable=False, index=True)
    permission_id = Column(String(36), ForeignKey("permissions.id"), nullable=False, index=True)

    role = relationship("Role", back_populates="permissions")
    permission = relationship("Permission", back_populates="role_permissions")

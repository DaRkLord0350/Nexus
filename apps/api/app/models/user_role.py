from sqlalchemy import Column, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import relationship

from app.db import Base
from app.models.base import TimestampMixin, TenantMixin


class UserRole(Base, TimestampMixin, TenantMixin):
    __tablename__ = "user_roles"
    __table_args__ = (UniqueConstraint("user_id", "role_id", name="uq_user_role"),)

    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    role_id = Column(String(36), ForeignKey("roles.id"), nullable=False, index=True)

    user = relationship("User", back_populates="roles")
    role = relationship("Role", back_populates="user_roles")

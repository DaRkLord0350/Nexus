from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String, Text, UniqueConstraint

from app.db import Base
from app.models.base import TimestampMixin, TenantMixin


class Customer(Base, TimestampMixin, TenantMixin):
    __tablename__ = "customers"
    __table_args__ = (
        UniqueConstraint("organization_id", "email", name="uq_customer_organization_email"),
    )

    email = Column(String(255), nullable=False, index=True)
    hashed_password = Column(String(255), nullable=True)
    first_name = Column(String(128), nullable=False)
    last_name = Column(String(128), nullable=False)
    phone = Column(String(50), nullable=True)
    is_guest = Column(Boolean, nullable=False, default=True)
    is_active = Column(Boolean, nullable=False, default=True)
    is_verified = Column(Boolean, nullable=False, default=False)
    accepts_marketing = Column(Boolean, nullable=False, default=False)
    last_login_at = Column(DateTime, nullable=True)
    notes = Column(Text, nullable=True)
    created_by = Column(String(36), ForeignKey("users.id"), nullable=True, index=True)

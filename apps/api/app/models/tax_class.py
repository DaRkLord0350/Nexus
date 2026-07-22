from sqlalchemy import Boolean, Column, ForeignKey, String, Text, UniqueConstraint

from app.db import Base
from app.models.base import TimestampMixin, TenantMixin


class TaxClass(Base, TimestampMixin, TenantMixin):
    __tablename__ = "tax_classes"
    __table_args__ = (
        UniqueConstraint("organization_id", "code", name="uq_tax_class_organization_code"),
    )

    name = Column(String(255), nullable=False)
    code = Column(String(64), nullable=False, index=True)
    description = Column(Text, nullable=True)
    is_default = Column(Boolean, nullable=False, default=False)
    is_active = Column(Boolean, nullable=False, default=True)
    created_by = Column(String(36), ForeignKey("users.id"), nullable=True, index=True)

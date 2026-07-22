from sqlalchemy import Column, String, UniqueConstraint

from app.db import Base
from app.models.base import TimestampMixin, TenantMixin


class QRCode(Base, TimestampMixin, TenantMixin):
    __tablename__ = "qr_codes"
    __table_args__ = (
        UniqueConstraint("organization_id", "entity_type", "entity_id", name="uq_qr_code_organization_entity"),
    )

    entity_type = Column(String(32), nullable=False, index=True)
    entity_id = Column(String(36), nullable=False, index=True)
    value = Column(String(255), nullable=False)
    image_url = Column(String(1024), nullable=True)

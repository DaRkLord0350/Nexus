from sqlalchemy import Column, String, UniqueConstraint

from app.db import Base
from app.models.base import TimestampMixin, TenantMixin


class Tag(Base, TimestampMixin, TenantMixin):
    __tablename__ = "tags"
    __table_args__ = (
        UniqueConstraint("organization_id", "slug", name="uq_tag_organization_slug"),
    )

    name = Column(String(100), nullable=False)
    slug = Column(String(100), nullable=False, index=True)

from sqlalchemy import Column, String

from app.db import Base
from app.models.base import TimestampMixin, TenantMixin


class SlugRedirect(Base, TimestampMixin, TenantMixin):
    __tablename__ = "slug_redirects"

    entity_type = Column(String(32), nullable=False, index=True)
    old_slug = Column(String(1024), nullable=False, index=True)
    new_slug = Column(String(1024), nullable=False)

from datetime import datetime
from uuid import uuid4

from sqlalchemy import Column, DateTime, ForeignKey, String
from sqlalchemy.orm import declared_attr


class TimestampMixin:
    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    deleted_at = Column(DateTime, nullable=True)


class TenantMixin:
    @declared_attr
    def organization_id(cls):
        return Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)

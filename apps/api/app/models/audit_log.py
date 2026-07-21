from sqlalchemy import Column, ForeignKey, JSON, String

from app.db import Base
from app.models.base import TenantMixin, TimestampMixin


class AuditLog(Base, TimestampMixin, TenantMixin):
    __tablename__ = "audit_logs"

    user_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    action = Column(String(64), nullable=False, index=True)
    module = Column(String(64), nullable=False, index=True)
    entity = Column(String(128), nullable=True, index=True)
    entity_id = Column(String(36), nullable=True, index=True)
    before = Column(JSON, nullable=True)
    after = Column(JSON, nullable=True)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(512), nullable=True)
    request_id = Column(String(64), nullable=True, index=True)

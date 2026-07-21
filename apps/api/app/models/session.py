from datetime import datetime
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String
from sqlalchemy.orm import relationship

from app.db import Base
from app.models.base import TimestampMixin, TenantMixin


class Session(Base, TimestampMixin, TenantMixin):
    __tablename__ = "sessions"

    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    device_name = Column(String(255), nullable=True)
    device_type = Column(String(64), nullable=True)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(512), nullable=True)
    last_active_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    revoked = Column(Boolean, default=False, nullable=False)

    user = relationship("User", back_populates="sessions")

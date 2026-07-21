from enum import Enum as PyEnum
from sqlalchemy import Boolean, Column, DateTime, Enum, ForeignKey, JSON, String, Text
from sqlalchemy.orm import relationship

from app.db import Base
from app.models.base import TimestampMixin, TenantMixin


class NotificationType(str, PyEnum):
    success = "success"
    warning = "warning"
    error = "error"
    info = "info"


class NotificationChannel(str, PyEnum):
    in_app = "in_app"
    email = "email"
    database = "database"
    sms = "sms"


class Notification(Base, TimestampMixin, TenantMixin):
    __tablename__ = "notifications"

    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    actor_id = Column(String(36), ForeignKey("users.id"), nullable=True, index=True)
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    type = Column(Enum(NotificationType), nullable=False)
    channel = Column(Enum(NotificationChannel), nullable=False, default=NotificationChannel.in_app)
    payload = Column(JSON, nullable=True)
    is_read = Column(Boolean, default=False, nullable=False)
    read_at = Column(DateTime, nullable=True)

    user = relationship("User", foreign_keys=[user_id])
    actor = relationship("User", foreign_keys=[actor_id])

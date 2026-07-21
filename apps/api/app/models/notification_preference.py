from enum import Enum as PyEnum
from sqlalchemy import Boolean, Column, DateTime, Enum, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import relationship

from app.db import Base
from app.models.base import TimestampMixin, TenantMixin


class NotificationChannel(str, PyEnum):
    in_app = "in_app"
    email = "email"
    sms = "sms"


class NotificationPreference(Base, TimestampMixin, TenantMixin):
    __tablename__ = "notification_preferences"
    __table_args__ = (UniqueConstraint("organization_id", "user_id", "channel", name="uq_notification_preference"),)

    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    channel = Column(Enum(NotificationChannel), nullable=False)
    enabled = Column(Boolean, nullable=False, default=True)

    user = relationship("User")

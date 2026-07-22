from enum import Enum as PyEnum

from sqlalchemy import Boolean, Column, Enum, ForeignKey, String, UniqueConstraint

from app.db import Base
from app.models.base import TimestampMixin, TenantMixin


class ChannelType(str, PyEnum):
    online_store = "online_store"
    pos = "pos"
    mobile_app = "mobile_app"
    marketplace = "marketplace"
    social = "social"
    other = "other"


class Channel(Base, TimestampMixin, TenantMixin):
    __tablename__ = "channels"
    __table_args__ = (
        UniqueConstraint("organization_id", "code", name="uq_channel_organization_code"),
    )

    name = Column(String(255), nullable=False)
    code = Column(String(64), nullable=False, index=True)
    channel_type = Column(Enum(ChannelType, native_enum=False), nullable=False, default=ChannelType.online_store)
    is_active = Column(Boolean, nullable=False, default=True)
    is_default = Column(Boolean, nullable=False, default=False)
    created_by = Column(String(36), ForeignKey("users.id"), nullable=True, index=True)

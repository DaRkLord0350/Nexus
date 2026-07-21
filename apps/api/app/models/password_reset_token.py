from datetime import datetime
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String
from sqlalchemy.orm import relationship

from app.db import Base
from app.models.base import TimestampMixin, TenantMixin


class PasswordResetToken(Base, TimestampMixin, TenantMixin):
    __tablename__ = "password_reset_tokens"

    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    token_hash = Column(String(128), nullable=False, unique=True, index=True)
    expires_at = Column(DateTime, nullable=False)
    revoked = Column(Boolean, default=False, nullable=False)

    user = relationship("User", back_populates="password_reset_tokens")

from datetime import datetime
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import relationship

from app.db import Base
from app.models.base import TimestampMixin, TenantMixin


class OrganizationInvitation(Base, TimestampMixin, TenantMixin):
    __tablename__ = "organization_invitations"

    email = Column(String(255), nullable=False, index=True)
    invited_by_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    token_hash = Column(String(128), nullable=False, unique=True, index=True)
    expires_at = Column(DateTime, nullable=False)
    accepted = Column(Boolean, default=False, nullable=False)
    revoked = Column(Boolean, default=False, nullable=False)
    accepted_at = Column(DateTime, nullable=True)

    invited_by = relationship("User")

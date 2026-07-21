from enum import Enum as PyEnum
from sqlalchemy import Column, Enum, String, Text
from sqlalchemy.orm import relationship

from app.db import Base
from app.models.base import TimestampMixin


class OrganizationStatus(str, PyEnum):
    active = "active"
    suspended = "suspended"
    deleted = "deleted"


class Organization(Base, TimestampMixin):
    __tablename__ = "organizations"

    name = Column(String(255), nullable=False, unique=True, index=True)
    slug = Column(String(255), nullable=False, unique=True, index=True)
    logo = Column(String(1024), nullable=True)
    industry = Column(String(128), nullable=True)
    country = Column(String(128), nullable=True)
    timezone = Column(String(64), nullable=True)
    currency = Column(String(16), nullable=True)
    subscription = Column(String(64), nullable=True)
    status = Column(Enum(OrganizationStatus, native_enum=False), default=OrganizationStatus.active, nullable=False)
    settings = Column(Text, nullable=True)

    members = relationship("User", back_populates="organization", cascade="all, delete-orphan")

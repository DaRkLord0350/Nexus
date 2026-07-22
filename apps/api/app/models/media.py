from enum import Enum as PyEnum

from sqlalchemy import BigInteger, Boolean, Column, Enum, ForeignKey, Integer, String

from app.db import Base
from app.models.base import TimestampMixin, TenantMixin
from app.models.file import StorageProvider


class MediaType(str, PyEnum):
    image = "image"
    video = "video"
    pdf = "pdf"
    model_3d = "model_3d"


class Media(Base, TimestampMixin, TenantMixin):
    __tablename__ = "media"

    product_id = Column(String(36), ForeignKey("products.id", ondelete="CASCADE"), nullable=True, index=True)
    variant_id = Column(String(36), ForeignKey("variants.id", ondelete="CASCADE"), nullable=True, index=True)
    media_type = Column(Enum(MediaType, native_enum=False), nullable=False, default=MediaType.image)
    object_key = Column(String(1024), nullable=False, unique=True, index=True)
    storage_provider = Column(Enum(StorageProvider, native_enum=False), nullable=False, default=StorageProvider.local)
    bucket = Column(String(255), nullable=True)
    content_type = Column(String(255), nullable=False)
    size_bytes = Column(BigInteger, nullable=False, default=0)
    checksum = Column(String(64), nullable=True, index=True)
    thumbnail_key = Column(String(1024), nullable=True)
    alt_text = Column(String(255), nullable=True)
    is_primary = Column(Boolean, nullable=False, default=False)
    sort_order = Column(Integer, nullable=False, default=0)
    uploaded_by = Column(String(36), ForeignKey("users.id"), nullable=True, index=True)

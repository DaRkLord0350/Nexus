from enum import Enum as PyEnum
from sqlalchemy import BigInteger, Column, Enum, ForeignKey, JSON, String
from sqlalchemy.orm import relationship

from app.db import Base
from app.models.base import TimestampMixin, TenantMixin


class StorageProvider(str, PyEnum):
    local = "local"
    s3 = "s3"


class FileVisibility(str, PyEnum):
    private = "private"
    public = "public"


class File(Base, TimestampMixin, TenantMixin):
    __tablename__ = "files"

    name = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=True)
    extension = Column(String(32), nullable=True)
    folder_id = Column(String(36), ForeignKey("folders.id"), nullable=True, index=True)
    object_key = Column(String(1024), nullable=False, unique=True, index=True)
    storage_provider = Column(Enum(StorageProvider, native_enum=False), nullable=False, default=StorageProvider.local)
    bucket = Column(String(255), nullable=True)
    content_type = Column(String(255), nullable=False)
    size_bytes = Column(BigInteger, nullable=False, default=0)
    checksum = Column(String(64), nullable=True, index=True)
    file_metadata = Column(JSON, nullable=True)
    visibility = Column(Enum(FileVisibility, native_enum=False), nullable=False, default=FileVisibility.private)
    uploaded_by = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)

    folder = relationship("Folder", back_populates="files")
    uploader = relationship("User", foreign_keys=[uploaded_by])

from sqlalchemy import Column, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import relationship

from app.db import Base
from app.models.base import TimestampMixin, TenantMixin


class Folder(Base, TimestampMixin, TenantMixin):
    __tablename__ = "folders"
    __table_args__ = (
        UniqueConstraint("organization_id", "parent_folder_id", "name", name="uq_folder_parent_name"),
    )

    name = Column(String(255), nullable=False)
    parent_folder_id = Column(String(36), ForeignKey("folders.id"), nullable=True, index=True)
    path = Column(String(1024), nullable=False, index=True)
    created_by = Column(String(36), ForeignKey("users.id"), nullable=True, index=True)

    files = relationship("File", back_populates="folder")

Folder.parent_folder = relationship("Folder", remote_side=[Folder.id], backref="children")

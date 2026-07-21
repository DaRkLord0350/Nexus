from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class StorageProvider(str, Enum):
    local = "local"
    s3 = "s3"


class FileVisibility(str, Enum):
    private = "private"
    public = "public"


class FolderCreateRequest(BaseModel):
    name: str = Field(..., min_length=1)
    parent_folder_id: str | None = None


class FolderUpdateRequest(BaseModel):
    name: str | None = None
    parent_folder_id: str | None = Field(default=None)
    move_to_root: bool = False


class FolderItem(BaseModel):
    id: str
    name: str
    path: str
    parent_folder_id: str | None = None
    created_by: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {
        "from_attributes": True,
    }


class FileItem(BaseModel):
    id: str
    name: str
    original_filename: str | None = None
    extension: str | None = None
    folder_id: str | None = None
    object_key: str
    storage_provider: StorageProvider
    bucket: str | None = None
    content_type: str
    size_bytes: int
    checksum: str | None = None
    file_metadata: dict[str, Any] | None = None
    visibility: FileVisibility
    uploaded_by: str
    created_at: datetime
    updated_at: datetime

    model_config = {
        "from_attributes": True,
    }


class UploadFileResponse(BaseModel):
    file: FileItem


class FileListResponse(BaseModel):
    files: list[FileItem]


class SignedUrlResponse(BaseModel):
    signed_url: str


class FileRenameRequest(BaseModel):
    name: str = Field(..., min_length=1)


class FileMoveRequest(BaseModel):
    folder_id: str | None = None


class SearchResponse(BaseModel):
    files: list[FileItem]
    folders: list[FolderItem]


class BreadcrumbItem(BaseModel):
    id: str
    name: str

    model_config = {
        "from_attributes": True,
    }

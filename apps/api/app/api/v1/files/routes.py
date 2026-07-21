from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, status, UploadFile
from fastapi.responses import FileResponse, RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit_context import AuditContext
from app.core.config import settings
from app.dependencies import get_audit_context, get_current_active_user, get_current_user_optional, get_db, require_permission
from app.schemas.file import (
    BreadcrumbItem,
    FileItem,
    FileListResponse,
    FileMoveRequest,
    FileRenameRequest,
    FolderCreateRequest,
    FolderItem,
    FolderUpdateRequest,
    SearchResponse,
    SignedUrlResponse,
    UploadFileResponse,
)
from app.services.audit_service import AuditService
from app.services.file_service import FileService
from app.models.file import FileVisibility, StorageProvider

router = APIRouter(prefix="/files", tags=["files"])


def _file_service(db: AsyncSession, current_user) -> FileService:
    return FileService(db, current_user.organization_id, current_user.is_superuser)


@router.post("/upload", response_model=FileItem)
async def upload_file(
    file: UploadFile = File(...),
    folder_id: str | None = Form(None),
    metadata: str | None = Form(None),
    visibility: FileVisibility = Form(FileVisibility.private),
    allow_duplicate: bool = Form(False),
    current_user=Depends(require_permission("files")),
    db: AsyncSession = Depends(get_db),
    audit_context: AuditContext = Depends(get_audit_context),
):
    file_service = _file_service(db, current_user)
    uploaded = await file_service.upload_file(
        file,
        current_user.id,
        folder_id=folder_id,
        metadata=metadata,
        visibility=visibility,
        allow_duplicate=allow_duplicate,
    )
    await AuditService(db, current_user.organization_id).log(
        action="upload",
        module="files",
        entity="File",
        entity_id=uploaded.id,
        user_id=current_user.id,
        after={"name": uploaded.name, "size_bytes": uploaded.size_bytes, "folder_id": uploaded.folder_id},
        context=audit_context,
    )
    return uploaded


@router.get("/search", response_model=SearchResponse)
async def search(
    q: str = Query(..., min_length=1),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    current_user=Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    file_service = _file_service(db, current_user)
    return await file_service.search(q, limit=limit, offset=offset)


@router.get("/", response_model=FileListResponse)
async def list_files(
    folder_id: str | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    current_user=Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    file_service = _file_service(db, current_user)
    files = await file_service.list_files(folder_id=folder_id, limit=limit, offset=offset)
    return {"files": files}


@router.post("/folders", response_model=FolderItem)
async def create_folder(
    data: FolderCreateRequest,
    current_user=Depends(require_permission("files")),
    db: AsyncSession = Depends(get_db),
    audit_context: AuditContext = Depends(get_audit_context),
):
    file_service = _file_service(db, current_user)
    folder = await file_service.create_folder(name=data.name, parent_folder_id=data.parent_folder_id, created_by=current_user.id)
    await AuditService(db, current_user.organization_id).log(
        action="create",
        module="files",
        entity="Folder",
        entity_id=folder.id,
        user_id=current_user.id,
        after={"name": folder.name, "parent_folder_id": folder.parent_folder_id},
        context=audit_context,
    )
    return folder


@router.get("/folders", response_model=list[FolderItem])
async def list_folders(
    parent_folder_id: str | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    current_user=Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    file_service = _file_service(db, current_user)
    return await file_service.list_folders(parent_folder_id=parent_folder_id, limit=limit, offset=offset)


@router.get("/folders/{folder_id}/breadcrumbs", response_model=list[BreadcrumbItem])
async def folder_breadcrumbs(folder_id: str, current_user=Depends(get_current_active_user), db: AsyncSession = Depends(get_db)):
    file_service = _file_service(db, current_user)
    return await file_service.get_breadcrumbs(folder_id)


@router.patch("/folders/{folder_id}", response_model=FolderItem)
async def update_folder(
    folder_id: str,
    data: FolderUpdateRequest,
    current_user=Depends(require_permission("files")),
    db: AsyncSession = Depends(get_db),
    audit_context: AuditContext = Depends(get_audit_context),
):
    file_service = _file_service(db, current_user)
    folder = None
    changes: dict = {}
    if data.name:
        folder = await file_service.rename_folder(folder_id, data.name)
        changes["name"] = folder.name
    if data.parent_folder_id is not None or data.move_to_root:
        target = None if data.move_to_root else data.parent_folder_id
        folder = await file_service.move_folder(folder_id, target)
        changes["parent_folder_id"] = folder.parent_folder_id
    if folder is None:
        folder = await file_service.get_folder(folder_id)
        if not folder:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Folder not found.")
    else:
        await AuditService(db, current_user.organization_id).log(
            action="update",
            module="files",
            entity="Folder",
            entity_id=folder.id,
            user_id=current_user.id,
            after=changes,
            context=audit_context,
        )
    return folder


@router.delete("/folders/{folder_id}")
async def delete_folder(
    folder_id: str,
    recursive: bool = Query(False),
    current_user=Depends(require_permission("files")),
    db: AsyncSession = Depends(get_db),
    audit_context: AuditContext = Depends(get_audit_context),
):
    file_service = _file_service(db, current_user)
    await file_service.delete_folder(folder_id, recursive=recursive)
    await AuditService(db, current_user.organization_id).log(
        action="delete",
        module="files",
        entity="Folder",
        entity_id=folder_id,
        user_id=current_user.id,
        before={"recursive": recursive},
        context=audit_context,
    )
    return {"detail": "Folder deleted successfully."}


@router.get("/{file_id}", response_model=FileItem)
async def get_file(file_id: str, current_user=Depends(get_current_user_optional), db: AsyncSession = Depends(get_db)):
    file_service = FileService(db, current_user.organization_id if current_user else None, current_user.is_superuser if current_user else False)
    file_record = await file_service.get_file(file_id)
    if not file_record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found.")

    if file_record.visibility != "public":
        if not current_user or not (current_user.is_superuser or current_user.organization_id == file_record.organization_id):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized access request.")
    return file_record


@router.get("/{file_id}/download")
async def download_file(
    file_id: str,
    token: str | None = Query(None),
    current_user=Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db),
    audit_context: AuditContext = Depends(get_audit_context),
):
    file_service = FileService(db, None, False)
    file_record = await file_service.get_file(file_id)
    if not file_record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found.")

    authorized = file_record.visibility == "public"
    if not authorized and token:
        token_file_id = file_service.verify_download_token(token)
        authorized = token_file_id == file_id
    elif not authorized and current_user:
        authorized = current_user.is_superuser or current_user.organization_id == file_record.organization_id

    if not authorized:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized download request.")

    await AuditService(db, file_record.organization_id).log(
        action="download",
        module="files",
        entity="File",
        entity_id=file_record.id,
        user_id=current_user.id if current_user else None,
        context=audit_context,
    )

    if file_record.storage_provider == StorageProvider.local:
        path = Path(settings.local_upload_path) / file_record.object_key
        if not path.exists():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found on disk.")
        return FileResponse(path, media_type=file_record.content_type, filename=file_record.name)

    signed_url = await file_service.get_signed_url(file_record)
    return RedirectResponse(url=signed_url)


@router.get("/{file_id}/signed-url", response_model=SignedUrlResponse)
async def get_signed_url(file_id: str, expires_in: int = Query(3600, ge=60, le=86400), current_user=Depends(get_current_active_user), db: AsyncSession = Depends(get_db)):
    file_service = _file_service(db, current_user)
    file_record = await file_service.get_file(file_id)
    if not file_record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found.")
    return {"signed_url": await file_service.get_signed_url(file_record, expires_in=expires_in)}


@router.post("/{file_id}/replace", response_model=FileItem)
async def replace_file(
    file_id: str,
    file: UploadFile = File(...),
    metadata: str | None = Form(None),
    current_user=Depends(require_permission("files")),
    db: AsyncSession = Depends(get_db),
    audit_context: AuditContext = Depends(get_audit_context),
):
    file_service = _file_service(db, current_user)
    updated = await file_service.replace_file(file_id, file, current_user.id, metadata=metadata)
    await AuditService(db, current_user.organization_id).log(
        action="update",
        module="files",
        entity="File",
        entity_id=updated.id,
        user_id=current_user.id,
        after={"size_bytes": updated.size_bytes, "checksum": updated.checksum},
        context=audit_context,
    )
    return updated


@router.patch("/{file_id}", response_model=FileItem)
async def rename_file(
    file_id: str,
    data: FileRenameRequest,
    current_user=Depends(require_permission("files")),
    db: AsyncSession = Depends(get_db),
    audit_context: AuditContext = Depends(get_audit_context),
):
    file_service = _file_service(db, current_user)
    updated = await file_service.rename_file(file_id, data.name, current_user.id)
    await AuditService(db, current_user.organization_id).log(
        action="update",
        module="files",
        entity="File",
        entity_id=updated.id,
        user_id=current_user.id,
        after={"name": updated.name},
        context=audit_context,
    )
    return updated


@router.post("/{file_id}/move", response_model=FileItem)
async def move_file(
    file_id: str,
    data: FileMoveRequest,
    current_user=Depends(require_permission("files")),
    db: AsyncSession = Depends(get_db),
    audit_context: AuditContext = Depends(get_audit_context),
):
    file_service = _file_service(db, current_user)
    updated = await file_service.move_file(file_id, data.folder_id, current_user.id)
    await AuditService(db, current_user.organization_id).log(
        action="update",
        module="files",
        entity="File",
        entity_id=updated.id,
        user_id=current_user.id,
        after={"folder_id": updated.folder_id},
        context=audit_context,
    )
    return updated


@router.delete("/{file_id}")
async def delete_file(
    file_id: str,
    current_user=Depends(require_permission("files")),
    db: AsyncSession = Depends(get_db),
    audit_context: AuditContext = Depends(get_audit_context),
):
    file_service = _file_service(db, current_user)
    await file_service.delete_file(file_id, current_user.id)
    await AuditService(db, current_user.organization_id).log(
        action="delete",
        module="files",
        entity="File",
        entity_id=file_id,
        user_id=current_user.id,
        context=audit_context,
    )
    return {"detail": "File deleted successfully."}

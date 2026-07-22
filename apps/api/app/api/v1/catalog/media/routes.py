from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from fastapi.responses import FileResponse, RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit_context import AuditContext
from app.core.config import settings
from app.dependencies import get_audit_context, get_current_active_user, get_current_user_optional, get_db, require_permission
from app.models.media import MediaType as ModelMediaType
from app.models.file import StorageProvider
from app.schemas.media import MediaItem, MediaListResponse, MediaType, MediaUpdateRequest, ReorderRequest, SignedUrlResponse
from app.services.audit_service import AuditService
from app.services.media_service import MediaService

router = APIRouter(prefix="/media", tags=["catalog-media"])


def _media_service(db: AsyncSession, current_user) -> MediaService:
    return MediaService(db, current_user.organization_id, current_user.is_superuser)


@router.post("/upload", response_model=MediaItem, status_code=status.HTTP_201_CREATED)
async def upload_media(
    file: UploadFile = File(...),
    product_id: str | None = Form(None),
    variant_id: str | None = Form(None),
    media_type: MediaType = Form(MediaType.image),
    alt_text: str | None = Form(None),
    is_primary: bool = Form(False),
    current_user=Depends(require_permission("catalog.media.manage")),
    db: AsyncSession = Depends(get_db),
    audit_context: AuditContext = Depends(get_audit_context),
):
    service = _media_service(db, current_user)
    media = await service.upload_media(
        file, current_user.id, product_id=product_id, variant_id=variant_id,
        media_type=ModelMediaType(media_type.value), alt_text=alt_text, is_primary=is_primary,
    )
    await AuditService(db, current_user.organization_id).log(
        action="upload", module="catalog", entity="Media", entity_id=media.id,
        user_id=current_user.id, after={"product_id": product_id, "variant_id": variant_id, "media_type": media_type.value}, context=audit_context,
    )
    return media


@router.get("/product/{product_id}", response_model=MediaListResponse)
async def list_media_for_product(
    product_id: str,
    current_user=Depends(require_permission("catalog.products.view")),
    db: AsyncSession = Depends(get_db),
):
    service = _media_service(db, current_user)
    return {"items": await service.list_for_product(product_id)}


@router.get("/variant/{variant_id}", response_model=MediaListResponse)
async def list_media_for_variant(
    variant_id: str,
    current_user=Depends(require_permission("catalog.products.view")),
    db: AsyncSession = Depends(get_db),
):
    service = _media_service(db, current_user)
    return {"items": await service.list_for_variant(variant_id)}


@router.post("/reorder")
async def reorder_media(
    data: ReorderRequest,
    current_user=Depends(require_permission("catalog.media.manage")),
    db: AsyncSession = Depends(get_db),
):
    service = _media_service(db, current_user)
    await service.reorder(data.media_ids)
    return {"detail": "Media reordered successfully."}


@router.get("/{media_id}", response_model=MediaItem)
async def get_media(media_id: str, current_user=Depends(require_permission("catalog.products.view")), db: AsyncSession = Depends(get_db)):
    service = _media_service(db, current_user)
    media = await service.get_media(media_id)
    if not media:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Media not found.")
    return media


@router.get("/{media_id}/signed-url", response_model=SignedUrlResponse)
async def get_signed_url(media_id: str, expires_in: int = Query(3600, ge=60, le=86400), current_user=Depends(get_current_active_user), db: AsyncSession = Depends(get_db)):
    service = _media_service(db, current_user)
    media = await service.get_media(media_id)
    if not media:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Media not found.")
    return {"signed_url": await service.get_signed_url(media, expires_in=expires_in)}


@router.get("/{media_id}/download")
async def download_media(
    media_id: str,
    token: str | None = Query(None),
    current_user=Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db),
):
    service = MediaService(db, None, False)
    media = await service.get_media(media_id)
    if not media:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Media not found.")

    authorized = False
    if token:
        authorized = service.verify_download_token(token) == media_id
    elif current_user:
        authorized = current_user.is_superuser or current_user.organization_id == media.organization_id
    if not authorized:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized download request.")

    if media.storage_provider == StorageProvider.local:
        path = Path(settings.local_upload_path) / media.object_key
        if not path.exists():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Media not found on disk.")
        return FileResponse(path, media_type=media.content_type)

    signed_url = await service.get_signed_url(media)
    return RedirectResponse(url=signed_url)


@router.patch("/{media_id}", response_model=MediaItem)
async def update_media(
    media_id: str,
    data: MediaUpdateRequest,
    current_user=Depends(require_permission("catalog.media.manage")),
    db: AsyncSession = Depends(get_db),
    audit_context: AuditContext = Depends(get_audit_context),
):
    service = _media_service(db, current_user)
    changes = data.model_dump(exclude_unset=True)
    media = await service.update_media(media_id, data)
    await AuditService(db, current_user.organization_id).log(
        action="update", module="catalog", entity="Media", entity_id=media.id,
        user_id=current_user.id, after=changes, context=audit_context,
    )
    return media


@router.delete("/{media_id}")
async def delete_media(
    media_id: str,
    current_user=Depends(require_permission("catalog.media.manage")),
    db: AsyncSession = Depends(get_db),
    audit_context: AuditContext = Depends(get_audit_context),
):
    service = _media_service(db, current_user)
    await service.delete_media(media_id)
    await AuditService(db, current_user.organization_id).log(
        action="delete", module="catalog", entity="Media", entity_id=media_id,
        user_id=current_user.id, context=audit_context,
    )
    return {"detail": "Media deleted successfully."}

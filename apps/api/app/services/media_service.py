from uuid import uuid4

from fastapi import HTTPException, UploadFile, status

from app.core.config import settings
from app.models.media import Media, MediaType
from app.models.file import StorageProvider
from app.repositories.media_repository import MediaRepository
from app.repositories.product_repository import ProductRepository
from app.repositories.variant_repository import VariantRepository
from app.storage.factory import build_storage_adapter
from app.utils.file_streaming import stream_to_temp_with_checksum
from app.utils.file_utils import secure_filename
from app.utils.signed_download import generate_download_token, verify_download_token


class MediaService:
    def __init__(self, session, organization_id: str | None = None, is_superuser: bool = False):
        self.session = session
        self.organization_id = organization_id
        self.is_superuser = is_superuser
        self.repo = MediaRepository(session, organization_id, is_superuser)
        self.product_repo = ProductRepository(session, organization_id, is_superuser)
        self.variant_repo = VariantRepository(session, organization_id, is_superuser)
        self.storage_adapter = build_storage_adapter()
        self.storage_provider = StorageProvider(settings.storage_provider)

    async def _validate_owner(self, product_id: str | None, variant_id: str | None) -> None:
        if not product_id and not variant_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Either product_id or variant_id is required.")
        if product_id and not await self.product_repo.get_by_id(product_id):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found.")
        if variant_id:
            variant = await self.variant_repo.get_by_id(variant_id)
            if not variant:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Variant not found.")
            if product_id and variant.product_id != product_id:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Variant does not belong to the given product.")

    async def upload_media(
        self,
        uploaded_file: UploadFile,
        uploaded_by: str,
        product_id: str | None = None,
        variant_id: str | None = None,
        media_type: MediaType = MediaType.image,
        alt_text: str | None = None,
        is_primary: bool = False,
    ) -> Media:
        if not uploaded_file.filename:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing file name.")
        await self._validate_owner(product_id, variant_id)

        content_type = uploaded_file.content_type or "application/octet-stream"
        checksum, size_bytes, spooled = await stream_to_temp_with_checksum(uploaded_file, settings.file_upload_max_bytes)
        try:
            if size_bytes == 0:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="File is empty.")

            safe_name = secure_filename(uploaded_file.filename)
            object_key = f"{self.organization_id}/media/{uuid4().hex}/{safe_name}"
            spooled.seek(0)
            upload_result = await self.storage_adapter.upload_stream(object_key=object_key, file_obj=spooled, content_type=content_type)

            media = Media(
                product_id=product_id,
                variant_id=variant_id,
                media_type=media_type,
                object_key=upload_result.object_key,
                storage_provider=self.storage_provider,
                bucket=upload_result.bucket,
                content_type=content_type,
                size_bytes=size_bytes,
                checksum=checksum,
                alt_text=alt_text,
                is_primary=is_primary,
                uploaded_by=uploaded_by,
            )
            created = await self.repo.create(media)

            if is_primary and product_id:
                await self.repo.unset_primary_for_product(product_id, exclude_media_id=created.id)
                await self.session.commit()

            return created
        finally:
            spooled.close()

    async def update_media(self, media_id: str, data) -> Media:
        media = await self.repo.get_by_id(media_id)
        if not media:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Media not found.")

        changes = data.model_dump(exclude_unset=True)
        for field, value in changes.items():
            setattr(media, field, value)
        saved = await self.repo.save(media)

        if saved.is_primary and saved.product_id:
            await self.repo.unset_primary_for_product(saved.product_id, exclude_media_id=saved.id)
            await self.session.commit()

        return saved

    async def reorder(self, media_ids: list[str]) -> None:
        for index, media_id in enumerate(media_ids):
            await self.repo.reorder(media_id, index)
        await self.session.commit()

    async def delete_media(self, media_id: str) -> None:
        media = await self.repo.get_by_id(media_id)
        if not media:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Media not found.")
        await self.storage_adapter.delete_file(media.object_key, bucket=media.bucket)
        await self.repo.delete(media_id)

    async def bulk_delete(self, media_ids: list[str]) -> int:
        media_items = [await self.repo.get_by_id(media_id) for media_id in media_ids]
        for media in media_items:
            if media:
                await self.storage_adapter.delete_file(media.object_key, bucket=media.bucket)
        return await self.repo.bulk_delete(media_ids)

    async def get_media(self, media_id: str) -> Media | None:
        return await self.repo.get_by_id(media_id)

    async def list_for_product(self, product_id: str) -> list[Media]:
        if not await self.product_repo.get_by_id(product_id):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found.")
        return await self.repo.list_for_product(product_id)

    async def list_for_variant(self, variant_id: str) -> list[Media]:
        if not await self.variant_repo.get_by_id(variant_id):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Variant not found.")
        return await self.repo.list_for_variant(variant_id)

    async def get_signed_url(self, media: Media, expires_in: int = 3600) -> str:
        if media.storage_provider == StorageProvider.local:
            token = generate_download_token(media.id, expires_in)
            api_url = str(settings.api_url).rstrip("/")
            return f"{api_url}/api/v1/catalog/media/{media.id}/download?token={token}"
        return await self.storage_adapter.generate_presigned_url(object_key=media.object_key, bucket=media.bucket, expires_in=expires_in)

    def verify_download_token(self, token: str) -> str | None:
        return verify_download_token(token)

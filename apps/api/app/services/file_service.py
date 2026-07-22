import asyncio
import hashlib
import tempfile
from io import BytesIO
from pathlib import Path
from typing import IO
from uuid import uuid4

from fastapi import HTTPException, UploadFile, status
from PIL import Image, UnidentifiedImageError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.file import File, FileVisibility, StorageProvider
from app.models.folder import Folder
from app.repositories.file_repository import FileRepository
from app.repositories.folder_repository import FolderRepository
from app.storage.factory import build_storage_adapter
from app.utils.file_streaming import STREAM_CHUNK_SIZE, SPOOL_MAX_SIZE, stream_to_temp_with_checksum
from app.utils.file_utils import get_extension, parse_metadata, secure_filename
from app.utils.signed_download import generate_download_token, verify_download_token

IMAGE_OPTIMIZATION_MAX_BYTES = 15 * 1024 * 1024


class FileService:
    def __init__(self, session: AsyncSession, organization_id: str | None = None, is_superuser: bool = False):
        self.session = session
        self.organization_id = organization_id
        self.is_superuser = is_superuser
        self.file_repo = FileRepository(session, organization_id, is_superuser)
        self.folder_repo = FolderRepository(session, organization_id, is_superuser)
        self.storage_adapter = build_storage_adapter()
        self.storage_provider = StorageProvider(settings.storage_provider)

    # ------------------------------------------------------------------
    # Folders
    # ------------------------------------------------------------------
    async def create_folder(self, name: str, parent_folder_id: str | None = None, created_by: str | None = None) -> Folder:
        safe_name = secure_filename(name)
        parent_folder = None
        if parent_folder_id:
            parent_folder = await self.folder_repo.get_by_id(parent_folder_id)
            if not parent_folder:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Parent folder not found.")

        existing = await self.folder_repo.get_by_parent_and_name(parent_folder_id, safe_name)
        if existing:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="A folder with that name already exists in this location.")

        path = self._build_path(parent_folder, safe_name)
        folder = Folder(name=safe_name, parent_folder_id=parent_folder_id, path=path, created_by=created_by)
        return await self.folder_repo.create(folder)

    async def rename_folder(self, folder_id: str, new_name: str) -> Folder:
        folder = await self.folder_repo.get_by_id(folder_id)
        if not folder:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Folder not found.")

        safe_name = secure_filename(new_name)
        conflict = await self.folder_repo.get_by_parent_and_name(folder.parent_folder_id, safe_name)
        if conflict and conflict.id != folder.id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="A folder with that name already exists in this location.")

        parent_folder = await self.folder_repo.get_by_id(folder.parent_folder_id) if folder.parent_folder_id else None
        new_path = self._build_path(parent_folder, safe_name)
        await self._reparent_descendant_paths(folder, new_path)
        return await self.folder_repo.rename(folder_id, safe_name, new_path)

    async def move_folder(self, folder_id: str, target_parent_folder_id: str | None) -> Folder:
        folder = await self.folder_repo.get_by_id(folder_id)
        if not folder:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Folder not found.")

        if target_parent_folder_id == folder_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="A folder cannot be moved into itself.")

        target_parent = None
        if target_parent_folder_id:
            target_parent = await self.folder_repo.get_by_id(target_parent_folder_id)
            if not target_parent:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Target folder not found.")

            descendants = await self.folder_repo.list_descendants(folder_id)
            if target_parent_folder_id in {d.id for d in descendants}:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="A folder cannot be moved into its own subfolder.")

        conflict = await self.folder_repo.get_by_parent_and_name(target_parent_folder_id, folder.name)
        if conflict and conflict.id != folder.id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="A folder with that name already exists in the destination.")

        new_path = self._build_path(target_parent, folder.name)
        await self._reparent_descendant_paths(folder, new_path)
        return await self.folder_repo.move(folder_id, target_parent_folder_id, new_path)

    async def delete_folder(self, folder_id: str, recursive: bool = False) -> None:
        folder = await self.folder_repo.get_by_id(folder_id)
        if not folder:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Folder not found.")

        descendants = await self.folder_repo.list_descendants(folder_id)
        direct_file_count = await self.file_repo.count_in_folder(folder_id)

        if not recursive and (descendants or direct_file_count):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Folder is not empty. Pass recursive=true to delete its contents.")

        all_folder_ids = [folder_id] + [d.id for d in descendants]
        files_to_purge = await self.file_repo.list_in_folder_ids(all_folder_ids)
        for file_record in files_to_purge:
            await self.storage_adapter.delete_file(file_record.object_key, bucket=file_record.bucket)
            await self.file_repo.delete(file_record.id)

        for descendant in reversed(descendants):
            await self.folder_repo.delete(descendant.id)
        await self.folder_repo.delete(folder_id)

    async def list_folders(self, parent_folder_id: str | None = None, limit: int = 50, offset: int = 0) -> list[Folder]:
        return await self.folder_repo.list(parent_folder_id=parent_folder_id, limit=limit, offset=offset)

    async def get_folder(self, folder_id: str) -> Folder | None:
        return await self.folder_repo.get_by_id(folder_id)

    async def get_breadcrumbs(self, folder_id: str) -> list[Folder]:
        trail: list[Folder] = []
        current_id = folder_id
        visited: set[str] = set()
        while current_id and current_id not in visited:
            visited.add(current_id)
            folder = await self.folder_repo.get_by_id(current_id)
            if not folder:
                break
            trail.append(folder)
            current_id = folder.parent_folder_id
        return list(reversed(trail))

    def _build_path(self, parent_folder: Folder | None, name: str) -> str:
        return f"{parent_folder.path}/{name}" if parent_folder else name

    async def _reparent_descendant_paths(self, folder: Folder, new_path: str) -> None:
        old_prefix = folder.path
        descendants = await self.folder_repo.list_descendants(folder.id)
        for descendant in descendants:
            if descendant.path.startswith(old_prefix + "/"):
                await self.folder_repo.update_path(descendant.id, new_path + descendant.path[len(old_prefix):])

    # ------------------------------------------------------------------
    # Files
    # ------------------------------------------------------------------
    async def upload_file(
        self,
        uploaded_file: UploadFile,
        user_id: str,
        folder_id: str | None = None,
        metadata: str | None = None,
        visibility: FileVisibility = FileVisibility.private,
        allow_duplicate: bool = False,
    ) -> File:
        if not uploaded_file.filename:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing file name.")

        content_type = uploaded_file.content_type or "application/octet-stream"
        if content_type not in settings.allowed_file_mime_types:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported file type.")

        folder = None
        if folder_id:
            folder = await self.folder_repo.get_by_id(folder_id)
            if not folder:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Folder not found.")

        checksum, size_bytes, spooled = await stream_to_temp_with_checksum(uploaded_file, settings.file_upload_max_bytes)
        try:
            if size_bytes == 0:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="File is empty.")

            await self._scan_stream(spooled)

            if settings.image_optimization_enabled and content_type.startswith("image/") and size_bytes <= IMAGE_OPTIMIZATION_MAX_BYTES:
                spooled, size_bytes, checksum = await self._optimize_image_stream(spooled, content_type)

            existing_duplicate = await self.file_repo.get_by_checksum(checksum, folder.id if folder else None)
            if existing_duplicate and not allow_duplicate:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail={
                        "message": "A file with identical contents already exists in this folder.",
                        "existing_file_id": existing_duplicate.id,
                        "existing_file_name": existing_duplicate.name,
                    },
                )

            safe_name = secure_filename(uploaded_file.filename)
            object_key = f"{self.organization_id}/{uuid4().hex}/{safe_name}"
            spooled.seek(0)
            upload_result = await self.storage_adapter.upload_stream(object_key=object_key, file_obj=spooled, content_type=content_type)

            file_metadata = parse_metadata(metadata) if isinstance(metadata, str) else None
            file_record = File(
                name=safe_name,
                original_filename=uploaded_file.filename,
                extension=get_extension(uploaded_file.filename),
                folder_id=folder.id if folder else None,
                object_key=upload_result.object_key,
                storage_provider=self.storage_provider,
                bucket=upload_result.bucket,
                content_type=content_type,
                size_bytes=size_bytes,
                checksum=checksum,
                file_metadata=file_metadata,
                visibility=visibility,
                uploaded_by=user_id,
            )
            return await self.file_repo.create(file_record)
        finally:
            spooled.close()

    async def replace_file(self, file_id: str, uploaded_file: UploadFile, user_id: str, metadata: str | None = None) -> File:
        existing = await self.file_repo.get_by_id(file_id)
        if not existing:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found.")
        if existing.uploaded_by != user_id and not self.is_superuser:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied.")

        content_type = uploaded_file.content_type or existing.content_type
        if content_type not in settings.allowed_file_mime_types:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported file type.")

        checksum, size_bytes, spooled = await stream_to_temp_with_checksum(uploaded_file, settings.file_upload_max_bytes)
        try:
            if size_bytes == 0:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="File is empty.")

            await self._scan_stream(spooled)

            if settings.image_optimization_enabled and content_type.startswith("image/") and size_bytes <= IMAGE_OPTIMIZATION_MAX_BYTES:
                spooled, size_bytes, checksum = await self._optimize_image_stream(spooled, content_type)

            safe_name = secure_filename(uploaded_file.filename or existing.name)
            object_key = f"{self.organization_id}/{uuid4().hex}/{safe_name}"
            spooled.seek(0)
            upload_result = await self.storage_adapter.upload_stream(object_key=object_key, file_obj=spooled, content_type=content_type)
            await self.storage_adapter.delete_file(existing.object_key, bucket=existing.bucket)

            file_metadata = parse_metadata(metadata) if isinstance(metadata, str) else existing.file_metadata
            return await self.file_repo.replace(
                file_id,
                upload_result.object_key,
                upload_result.bucket,
                content_type,
                size_bytes,
                file_metadata,
                checksum=checksum,
            )
        finally:
            spooled.close()

    async def delete_file(self, file_id: str, user_id: str) -> None:
        existing = await self.file_repo.get_by_id(file_id)
        if not existing:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found.")
        if existing.uploaded_by != user_id and not self.is_superuser:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied.")

        await self.storage_adapter.delete_file(existing.object_key, bucket=existing.bucket)
        await self.file_repo.delete(file_id)

    async def rename_file(self, file_id: str, new_name: str, user_id: str) -> File:
        existing = await self.file_repo.get_by_id(file_id)
        if not existing:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found.")
        if existing.uploaded_by != user_id and not self.is_superuser:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied.")

        safe_name = secure_filename(new_name)
        return await self.file_repo.rename(file_id, safe_name, get_extension(safe_name))

    async def move_file(self, file_id: str, target_folder_id: str | None, user_id: str) -> File:
        existing = await self.file_repo.get_by_id(file_id)
        if not existing:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found.")
        if existing.uploaded_by != user_id and not self.is_superuser:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied.")

        if target_folder_id:
            target_folder = await self.folder_repo.get_by_id(target_folder_id)
            if not target_folder:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Target folder not found.")

        return await self.file_repo.move(file_id, target_folder_id)

    async def list_files(self, folder_id: str | None = None, limit: int = 50, offset: int = 0) -> list[File]:
        return await self.file_repo.list(folder_id=folder_id, limit=limit, offset=offset)

    async def get_file(self, file_id: str) -> File | None:
        return await self.file_repo.get_by_id(file_id)

    async def search(self, query: str, limit: int = 50, offset: int = 0) -> dict[str, list]:
        files = await self.file_repo.search(query, limit=limit, offset=offset)
        folders = await self.folder_repo.search(query, limit=limit, offset=offset)
        return {"files": files, "folders": folders}

    async def get_signed_url(self, file: File, expires_in: int = 3600) -> str:
        if file.storage_provider == StorageProvider.local:
            token = generate_download_token(file.id, expires_in)
            api_url = str(settings.api_url).rstrip("/")
            return f"{api_url}/api/v1/files/{file.id}/download?token={token}"

        return await self.storage_adapter.generate_presigned_url(object_key=file.object_key, bucket=file.bucket, expires_in=expires_in)

    def verify_download_token(self, token: str) -> str | None:
        return verify_download_token(token)

    # ------------------------------------------------------------------
    # Streaming, scanning, optimization
    # ------------------------------------------------------------------
    async def _scan_stream(self, spooled: IO[bytes]) -> None:
        if not settings.virus_scan_command:
            return

        spooled.seek(0)
        process = await asyncio.create_subprocess_shell(
            settings.virus_scan_command,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        try:
            while True:
                chunk = await asyncio.to_thread(spooled.read, STREAM_CHUNK_SIZE)
                if not chunk:
                    break
                process.stdin.write(chunk)
                await process.stdin.drain()
            process.stdin.close()
            stdout, stderr = await process.communicate()
        finally:
            spooled.seek(0)

        if process.returncode != 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Virus scan failed: {stderr.decode('utf-8', errors='ignore')}",
            )

    async def _optimize_image_stream(self, spooled: IO[bytes], content_type: str) -> tuple[IO[bytes], int, str]:
        spooled.seek(0)
        data = await asyncio.to_thread(spooled.read)
        try:
            optimized = await asyncio.to_thread(self._optimize_image_sync, data)
        except UnidentifiedImageError:
            spooled.seek(0)
            return spooled, len(data), hashlib.sha256(data).hexdigest()

        new_spooled = tempfile.SpooledTemporaryFile(max_size=SPOOL_MAX_SIZE)
        await asyncio.to_thread(new_spooled.write, optimized)
        new_spooled.seek(0)
        spooled.close()
        return new_spooled, len(optimized), hashlib.sha256(optimized).hexdigest()

    def _optimize_image_sync(self, file_bytes: bytes) -> bytes:
        image = Image.open(BytesIO(file_bytes))
        image = image.convert("RGB")
        output = BytesIO()
        image.save(output, format="JPEG", quality=settings.image_optimization_quality, optimize=True)
        return output.getvalue()

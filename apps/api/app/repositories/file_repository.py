from __future__ import annotations

from sqlalchemy import delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.file import File
from app.repositories.base_repository import BaseRepository


class FileRepository(BaseRepository):
    def __init__(self, session: AsyncSession, organization_id: str | None = None, is_superuser: bool = False):
        super().__init__(session, organization_id, is_superuser)

    async def create(self, file_record: File) -> File:
        self._add_tenant_on_create(file_record)
        self.session.add(file_record)
        await self.session.commit()
        await self.session.refresh(file_record)
        return file_record

    async def get_by_id(self, file_id: str) -> File | None:
        statement = select(File).where(File.id == file_id)
        statement = self._apply_tenant_filter(statement, File)
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def list(self, folder_id: str | None = None, limit: int = 50, offset: int = 0) -> list[File]:
        statement = select(File).order_by(File.created_at.desc()).limit(limit).offset(offset)
        if folder_id is not None:
            statement = statement.where(File.folder_id == folder_id)
        statement = self._apply_tenant_filter(statement, File)
        result = await self.session.execute(statement)
        return result.scalars().all()

    async def delete(self, file_id: str) -> None:
        statement = delete(File).where(File.id == file_id)
        statement = self._apply_tenant_filter(statement, File)
        await self.session.execute(statement)
        await self.session.commit()

    async def replace(self, file_id: str, object_key: str, bucket: str | None, content_type: str, size_bytes: int, file_metadata: dict | None, checksum: str | None = None) -> File:
        statement = (
            update(File)
            .where(File.id == file_id)
            .values(object_key=object_key, bucket=bucket, content_type=content_type, size_bytes=size_bytes, file_metadata=file_metadata, checksum=checksum)
            .execution_options(synchronize_session="fetch")
        )
        statement = self._apply_tenant_filter(statement, File)
        await self.session.execute(statement)
        await self.session.commit()
        return await self.get_by_id(file_id)

    async def get_by_checksum(self, checksum: str, folder_id: str | None) -> File | None:
        statement = select(File).where(File.checksum == checksum)
        statement = statement.where(File.folder_id == folder_id) if folder_id is not None else statement.where(File.folder_id.is_(None))
        statement = self._apply_tenant_filter(statement, File)
        result = await self.session.execute(statement)
        return result.scalars().first()

    async def move(self, file_id: str, folder_id: str | None) -> File:
        statement = (
            update(File)
            .where(File.id == file_id)
            .values(folder_id=folder_id)
            .execution_options(synchronize_session="fetch")
        )
        statement = self._apply_tenant_filter(statement, File)
        await self.session.execute(statement)
        await self.session.commit()
        return await self.get_by_id(file_id)

    async def rename(self, file_id: str, name: str, extension: str) -> File:
        statement = (
            update(File)
            .where(File.id == file_id)
            .values(name=name, extension=extension)
            .execution_options(synchronize_session="fetch")
        )
        statement = self._apply_tenant_filter(statement, File)
        await self.session.execute(statement)
        await self.session.commit()
        return await self.get_by_id(file_id)

    async def search(self, query: str, limit: int = 50, offset: int = 0) -> list[File]:
        statement = (
            select(File)
            .where(File.name.ilike(f"%{query}%"))
            .order_by(File.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        statement = self._apply_tenant_filter(statement, File)
        result = await self.session.execute(statement)
        return result.scalars().all()

    async def count_in_folder(self, folder_id: str) -> int:
        statement = select(func.count(File.id)).where(File.folder_id == folder_id)
        statement = self._apply_tenant_filter(statement, File)
        result = await self.session.execute(statement)
        return result.scalar_one()

    async def list_in_folder_ids(self, folder_ids: list[str]) -> list[File]:
        if not folder_ids:
            return []
        statement = select(File).where(File.folder_id.in_(folder_ids))
        statement = self._apply_tenant_filter(statement, File)
        result = await self.session.execute(statement)
        return result.scalars().all()

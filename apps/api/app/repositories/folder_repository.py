from __future__ import annotations

from sqlalchemy import delete as sa_delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.folder import Folder
from app.repositories.base_repository import BaseRepository


class FolderRepository(BaseRepository):
    def __init__(self, session: AsyncSession, organization_id: str | None = None, is_superuser: bool = False):
        super().__init__(session, organization_id, is_superuser)

    async def create(self, folder: Folder) -> Folder:
        self._add_tenant_on_create(folder)
        self.session.add(folder)
        await self.session.commit()
        await self.session.refresh(folder)
        return folder

    async def get_by_id(self, folder_id: str) -> Folder | None:
        statement = select(Folder).where(Folder.id == folder_id)
        statement = self._apply_tenant_filter(statement, Folder)
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def list(self, parent_folder_id: str | None = None, limit: int = 50, offset: int = 0) -> list[Folder]:
        statement = select(Folder).order_by(Folder.name.asc()).limit(limit).offset(offset)
        if parent_folder_id is not None:
            statement = statement.where(Folder.parent_folder_id == parent_folder_id)
        else:
            statement = statement.where(Folder.parent_folder_id.is_(None))
        statement = self._apply_tenant_filter(statement, Folder)
        result = await self.session.execute(statement)
        return result.scalars().all()

    async def get_by_path(self, path: str) -> Folder | None:
        statement = select(Folder).where(Folder.path == path)
        statement = self._apply_tenant_filter(statement, Folder)
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def get_by_parent_and_name(self, parent_folder_id: str | None, name: str) -> Folder | None:
        statement = select(Folder).where(Folder.name == name)
        statement = statement.where(Folder.parent_folder_id == parent_folder_id) if parent_folder_id is not None else statement.where(Folder.parent_folder_id.is_(None))
        statement = self._apply_tenant_filter(statement, Folder)
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def list_children(self, folder_id: str) -> list[Folder]:
        statement = select(Folder).where(Folder.parent_folder_id == folder_id)
        statement = self._apply_tenant_filter(statement, Folder)
        result = await self.session.execute(statement)
        return result.scalars().all()

    async def list_descendants(self, folder_id: str) -> list[Folder]:
        descendants: list[Folder] = []
        frontier = [folder_id]
        while frontier:
            next_frontier: list[str] = []
            for current_id in frontier:
                children = await self.list_children(current_id)
                descendants.extend(children)
                next_frontier.extend(child.id for child in children)
            frontier = next_frontier
        return descendants

    async def update_path(self, folder_id: str, path: str) -> None:
        statement = update(Folder).where(Folder.id == folder_id).values(path=path)
        statement = self._apply_tenant_filter(statement, Folder)
        await self.session.execute(statement)

    async def rename(self, folder_id: str, name: str, path: str) -> Folder:
        statement = update(Folder).where(Folder.id == folder_id).values(name=name, path=path)
        statement = self._apply_tenant_filter(statement, Folder)
        await self.session.execute(statement)
        await self.session.commit()
        return await self.get_by_id(folder_id)

    async def move(self, folder_id: str, parent_folder_id: str | None, path: str) -> Folder:
        statement = update(Folder).where(Folder.id == folder_id).values(parent_folder_id=parent_folder_id, path=path)
        statement = self._apply_tenant_filter(statement, Folder)
        await self.session.execute(statement)
        await self.session.commit()
        return await self.get_by_id(folder_id)

    async def delete(self, folder_id: str) -> None:
        statement = sa_delete(Folder).where(Folder.id == folder_id)
        statement = self._apply_tenant_filter(statement, Folder)
        await self.session.execute(statement)
        await self.session.commit()

    async def search(self, query: str, limit: int = 50, offset: int = 0) -> list[Folder]:
        statement = select(Folder).where(Folder.name.ilike(f"%{query}%")).order_by(Folder.name.asc()).limit(limit).offset(offset)
        statement = self._apply_tenant_filter(statement, Folder)
        result = await self.session.execute(statement)
        return result.scalars().all()

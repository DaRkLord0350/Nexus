import asyncio

import pytest
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.db import Base
from app.schemas.category import CategoryCreateRequest, CategoryUpdateRequest
from app.services.auth_service import AuthService
from app.services.category_service import CategoryService


@pytest.fixture
def app_session(tmp_path) -> AsyncSession:
    database_url = f"sqlite+aiosqlite:///{tmp_path / 'test.db'}"
    engine = create_async_engine(database_url, future=True)

    async def initialize_database() -> None:
        async with engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)

    asyncio.run(initialize_database())
    async_session = async_sessionmaker(engine, expire_on_commit=False)
    session = async_session()

    try:
        yield session
    finally:
        asyncio.run(session.close())
        asyncio.run(engine.dispose())


async def _register_org(session):
    auth_service = AuthService(session)
    return await auth_service.register_user(
        email="owner@example.com",
        first_name="Ada",
        last_name="Lovelace",
        password="SecurePass456!",
        organization_name="Category Test Org",
    )


def test_create_category_generates_slug_and_path(app_session: AsyncSession):
    async def _run():
        user = await _register_org(app_session)
        service = CategoryService(app_session, organization_id=user.organization_id)

        category = await service.create_category(
            CategoryCreateRequest(name="Electronics"), created_by=user.id
        )
        assert category.slug == "electronics"
        assert category.path == "electronics"

        child = await service.create_category(
            CategoryCreateRequest(name="Phones", parent_id=category.id), created_by=user.id
        )
        assert child.path == "electronics/phones"
        assert child.parent_id == category.id

    asyncio.run(_run())


def test_duplicate_slug_rejected(app_session: AsyncSession):
    async def _run():
        user = await _register_org(app_session)
        service = CategoryService(app_session, organization_id=user.organization_id)
        await service.create_category(CategoryCreateRequest(name="Electronics"), created_by=user.id)

        with pytest.raises(HTTPException) as exc_info:
            await service.create_category(CategoryCreateRequest(name="Electronics"), created_by=user.id)
        assert exc_info.value.status_code == 400

    asyncio.run(_run())


def test_rename_updates_descendant_paths(app_session: AsyncSession):
    async def _run():
        user = await _register_org(app_session)
        service = CategoryService(app_session, organization_id=user.organization_id)

        parent = await service.create_category(CategoryCreateRequest(name="Electronics"), created_by=user.id)
        child = await service.create_category(
            CategoryCreateRequest(name="Phones", parent_id=parent.id), created_by=user.id
        )

        await service.update_category(parent.id, CategoryUpdateRequest(name="Gadgets"))
        refreshed_child = await service.get_category(child.id)
        assert refreshed_child.path == "gadgets/phones"

    asyncio.run(_run())


def test_delete_requires_cascade_when_children_exist(app_session: AsyncSession):
    async def _run():
        user = await _register_org(app_session)
        service = CategoryService(app_session, organization_id=user.organization_id)

        parent = await service.create_category(CategoryCreateRequest(name="Electronics"), created_by=user.id)
        await service.create_category(CategoryCreateRequest(name="Phones", parent_id=parent.id), created_by=user.id)

        with pytest.raises(HTTPException) as exc_info:
            await service.delete_category(parent.id)
        assert exc_info.value.status_code == 400

        await service.delete_category(parent.id, cascade=True)
        assert await service.get_category(parent.id) is None

    asyncio.run(_run())


def test_restore_category(app_session: AsyncSession):
    async def _run():
        user = await _register_org(app_session)
        service = CategoryService(app_session, organization_id=user.organization_id)

        category = await service.create_category(CategoryCreateRequest(name="Electronics"), created_by=user.id)
        await service.delete_category(category.id)
        assert await service.get_category(category.id) is None

        restored = await service.restore_category(category.id)
        assert restored.id == category.id
        assert await service.get_category(category.id) is not None

    asyncio.run(_run())


def test_tenant_isolation(app_session: AsyncSession):
    async def _run():
        user_a = await _register_org(app_session)
        auth_service = AuthService(app_session)
        user_b = await auth_service.register_user(
            email="owner-b@example.com",
            first_name="Grace",
            last_name="Hopper",
            password="SecurePass456!",
            organization_name="Second Org",
        )

        service_a = CategoryService(app_session, organization_id=user_a.organization_id)
        service_b = CategoryService(app_session, organization_id=user_b.organization_id)

        category = await service_a.create_category(CategoryCreateRequest(name="Electronics"), created_by=user_a.id)
        assert await service_b.get_category(category.id) is None

    asyncio.run(_run())

import asyncio
from io import BytesIO
from pathlib import Path

import pytest
from fastapi import HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from starlette.datastructures import UploadFile as StarletteUploadFile

from app.core.config import settings
from app.db import Base
from app.models.media import MediaType
from app.schemas.product import ProductCreateRequest
from app.services.auth_service import AuthService
from app.services.media_service import MediaService
from app.services.product_service import ProductService


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


def make_upload_file(filename: str, content: bytes, content_type: str) -> UploadFile:
    source = BytesIO(content)
    headers = {"content-type": content_type}
    return StarletteUploadFile(source, filename=filename, headers=headers)


async def _setup(session, tmp_path, email="owner@example.com", org_name="Media Test Org"):
    settings.local_upload_path = tmp_path / "uploads"
    auth_service = AuthService(session)
    user = await auth_service.register_user(
        email=email, first_name="Ada", last_name="Lovelace", password="SecurePass456!", organization_name=org_name,
    )
    product_service = ProductService(session, organization_id=user.organization_id)
    product = await product_service.create_product(ProductCreateRequest(name="T-Shirt", sku="TSHIRT-001"), created_by=user.id)
    return user, product


def test_upload_media_for_product(app_session: AsyncSession, tmp_path: Path):
    async def _run():
        user, product = await _setup(app_session, tmp_path)
        service = MediaService(app_session, organization_id=user.organization_id)
        upload_file = make_upload_file("hero.jpg", b"fake-image-bytes", "image/jpeg")

        media = await service.upload_media(upload_file, user.id, product_id=product.id, media_type=MediaType.image, is_primary=True)
        assert media.product_id == product.id
        assert media.is_primary is True
        assert (settings.local_upload_path / media.object_key).exists()

        items = await service.list_for_product(product.id)
        assert len(items) == 1

    asyncio.run(_run())


def test_only_one_primary_media_per_product(app_session: AsyncSession, tmp_path: Path):
    async def _run():
        user, product = await _setup(app_session, tmp_path)
        service = MediaService(app_session, organization_id=user.organization_id)

        m1 = await service.upload_media(make_upload_file("a.jpg", b"a", "image/jpeg"), user.id, product_id=product.id, is_primary=True)
        m2 = await service.upload_media(make_upload_file("b.jpg", b"b", "image/jpeg"), user.id, product_id=product.id, is_primary=True)

        refreshed_m1 = await service.get_media(m1.id)
        assert refreshed_m1.is_primary is False
        assert m2.is_primary is True

    asyncio.run(_run())


def test_upload_requires_product_or_variant(app_session: AsyncSession, tmp_path: Path):
    async def _run():
        user, _ = await _setup(app_session, tmp_path)
        service = MediaService(app_session, organization_id=user.organization_id)
        with pytest.raises(HTTPException) as exc_info:
            await service.upload_media(make_upload_file("a.jpg", b"a", "image/jpeg"), user.id)
        assert exc_info.value.status_code == 400

    asyncio.run(_run())


def test_delete_media_removes_storage_object(app_session: AsyncSession, tmp_path: Path):
    async def _run():
        user, product = await _setup(app_session, tmp_path)
        service = MediaService(app_session, organization_id=user.organization_id)
        media = await service.upload_media(make_upload_file("a.jpg", b"a", "image/jpeg"), user.id, product_id=product.id)

        object_path = settings.local_upload_path / media.object_key
        assert object_path.exists()

        await service.delete_media(media.id)
        assert await service.get_media(media.id) is None
        assert not object_path.exists()

    asyncio.run(_run())


def test_reorder_media(app_session: AsyncSession, tmp_path: Path):
    async def _run():
        user, product = await _setup(app_session, tmp_path)
        service = MediaService(app_session, organization_id=user.organization_id)
        m1 = await service.upload_media(make_upload_file("a.jpg", b"a", "image/jpeg"), user.id, product_id=product.id)
        m2 = await service.upload_media(make_upload_file("b.jpg", b"b", "image/jpeg"), user.id, product_id=product.id)

        await service.reorder([m2.id, m1.id])
        items = await service.list_for_product(product.id)
        assert [i.id for i in items] == [m2.id, m1.id]

    asyncio.run(_run())


def test_tenant_isolation(app_session: AsyncSession, tmp_path: Path):
    async def _run():
        user_a, product_a = await _setup(app_session, tmp_path, email="a@example.com", org_name="Org A")
        user_b, _ = await _setup(app_session, tmp_path, email="b@example.com", org_name="Org B")

        service_a = MediaService(app_session, organization_id=user_a.organization_id)
        service_b = MediaService(app_session, organization_id=user_b.organization_id)

        media = await service_a.upload_media(make_upload_file("a.jpg", b"a", "image/jpeg"), user_a.id, product_id=product_a.id)
        assert await service_b.get_media(media.id) is None

    asyncio.run(_run())

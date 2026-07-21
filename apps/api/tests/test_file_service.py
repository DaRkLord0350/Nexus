import asyncio
import hashlib
from io import BytesIO
from pathlib import Path

import pytest
from fastapi import HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from starlette.datastructures import UploadFile as StarletteUploadFile

from app.core.config import settings
from app.db import Base
from app.models.file import FileVisibility
from app.services.auth_service import AuthService
from app.services.file_service import FileService


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


def test_file_upload_and_delete(app_session: AsyncSession, tmp_path: Path):
    async def _run_test():
        settings.local_upload_path = tmp_path / "uploads"
        auth_service = AuthService(app_session)
        user = await auth_service.register_user(
            email="bob@example.com",
            first_name="Bob",
            last_name="Miller",
            password="SecurePass456!",
            organization_name="CommerceOS File Test",
        )

        file_service = FileService(app_session, organization_id=user.organization_id)
        upload_file = make_upload_file("report.pdf", b"hello world", "application/pdf")
        saved_file = await file_service.upload_file(upload_file, user.id)

        assert saved_file.id
        assert saved_file.storage_provider == "local"
        assert saved_file.size_bytes == 11
        assert (settings.local_upload_path / saved_file.object_key).exists()

        signed_url = await file_service.get_signed_url(saved_file, expires_in=300)
        assert "/api/v1/files/" in signed_url
        assert str(saved_file.id) in signed_url

        await file_service.delete_file(saved_file.id, user.id)
        assert await file_service.get_file(saved_file.id) is None
        assert not (settings.local_upload_path / saved_file.object_key).exists()

    asyncio.run(_run_test())


def test_checksum_and_duplicate_detection(app_session: AsyncSession, tmp_path: Path):
    async def _run_test():
        settings.local_upload_path = tmp_path / "uploads"
        auth_service = AuthService(app_session)
        user = await auth_service.register_user(
            email="dup@example.com",
            first_name="Dup",
            last_name="Tester",
            password="SecurePass456!",
            organization_name="Duplicate Detection Org",
        )
        file_service = FileService(app_session, organization_id=user.organization_id)

        first = await file_service.upload_file(make_upload_file("a.txt", b"identical bytes", "application/pdf"), user.id)
        assert first.checksum == hashlib.sha256(b"identical bytes").hexdigest()

        with pytest.raises(HTTPException) as exc_info:
            await file_service.upload_file(make_upload_file("b.txt", b"identical bytes", "application/pdf"), user.id)
        assert exc_info.value.status_code == 409

        second = await file_service.upload_file(
            make_upload_file("b.txt", b"identical bytes", "application/pdf"), user.id, allow_duplicate=True
        )
        assert second.id != first.id
        assert second.checksum == first.checksum

    asyncio.run(_run_test())


def test_move_and_rename_file(app_session: AsyncSession, tmp_path: Path):
    async def _run_test():
        settings.local_upload_path = tmp_path / "uploads"
        auth_service = AuthService(app_session)
        user = await auth_service.register_user(
            email="mover@example.com",
            first_name="Mover",
            last_name="Tester",
            password="SecurePass456!",
            organization_name="Move Rename Org",
        )
        file_service = FileService(app_session, organization_id=user.organization_id)

        folder = await file_service.create_folder("Reports", created_by=user.id)
        saved_file = await file_service.upload_file(make_upload_file("report.pdf", b"contents", "application/pdf"), user.id)

        moved = await file_service.move_file(saved_file.id, folder.id, user.id)
        assert moved.folder_id == folder.id

        renamed = await file_service.rename_file(saved_file.id, "final report.pdf", user.id)
        assert renamed.name == "final_report.pdf"
        assert renamed.extension == "pdf"

    asyncio.run(_run_test())


def test_file_move_rename_permission_denied_for_other_user(app_session: AsyncSession, tmp_path: Path):
    async def _run_test():
        settings.local_upload_path = tmp_path / "uploads"
        auth_service = AuthService(app_session)
        owner = await auth_service.register_user(
            email="owner@example.com",
            first_name="Owner",
            last_name="Tester",
            password="SecurePass456!",
            organization_name="Permission Org",
        )
        other_user = await auth_service.register_user(
            email="other@example.com",
            first_name="Other",
            last_name="Tester",
            password="SecurePass456!",
            organization_name="Permission Org Two",
        )

        owner_service = FileService(app_session, organization_id=owner.organization_id)
        saved_file = await owner_service.upload_file(make_upload_file("secret.pdf", b"secret", "application/pdf"), owner.id)

        intruding_service = FileService(app_session, organization_id=owner.organization_id)
        with pytest.raises(HTTPException) as exc_info:
            await intruding_service.rename_file(saved_file.id, "hijacked.pdf", other_user.id)
        assert exc_info.value.status_code == 403

        with pytest.raises(HTTPException) as exc_info:
            await intruding_service.delete_file(saved_file.id, other_user.id)
        assert exc_info.value.status_code == 403

    asyncio.run(_run_test())


def test_folder_delete_requires_recursive_when_not_empty(app_session: AsyncSession, tmp_path: Path):
    async def _run_test():
        settings.local_upload_path = tmp_path / "uploads"
        auth_service = AuthService(app_session)
        user = await auth_service.register_user(
            email="folders@example.com",
            first_name="Folder",
            last_name="Tester",
            password="SecurePass456!",
            organization_name="Folder Delete Org",
        )
        file_service = FileService(app_session, organization_id=user.organization_id)

        parent = await file_service.create_folder("Parent", created_by=user.id)
        child = await file_service.create_folder("Child", parent_folder_id=parent.id, created_by=user.id)
        saved_file = await file_service.upload_file(make_upload_file("nested.pdf", b"nested", "application/pdf"), user.id, folder_id=child.id)

        with pytest.raises(HTTPException) as exc_info:
            await file_service.delete_folder(parent.id, recursive=False)
        assert exc_info.value.status_code == 400

        await file_service.delete_folder(parent.id, recursive=True)
        assert await file_service.get_folder(parent.id) is None
        assert await file_service.get_folder(child.id) is None
        assert await file_service.get_file(saved_file.id) is None
        assert not (settings.local_upload_path / saved_file.object_key).exists()

    asyncio.run(_run_test())


def test_folder_rename_and_move_updates_descendant_paths(app_session: AsyncSession, tmp_path: Path):
    async def _run_test():
        settings.local_upload_path = tmp_path / "uploads"
        auth_service = AuthService(app_session)
        user = await auth_service.register_user(
            email="paths@example.com",
            first_name="Path",
            last_name="Tester",
            password="SecurePass456!",
            organization_name="Folder Path Org",
        )
        file_service = FileService(app_session, organization_id=user.organization_id)

        root_a = await file_service.create_folder("Alpha", created_by=user.id)
        root_b = await file_service.create_folder("Beta", created_by=user.id)
        child = await file_service.create_folder("Nested", parent_folder_id=root_a.id, created_by=user.id)

        renamed_root = await file_service.rename_folder(root_a.id, "Alpha Renamed")
        assert renamed_root.path == "Alpha_Renamed"
        updated_child = await file_service.get_folder(child.id)
        assert updated_child.path == "Alpha_Renamed/Nested"

        moved_child = await file_service.move_folder(child.id, root_b.id)
        assert moved_child.path == "Beta/Nested"

        with pytest.raises(HTTPException) as exc_info:
            await file_service.move_folder(root_b.id, moved_child.id)
        assert exc_info.value.status_code == 400

    asyncio.run(_run_test())


def test_tenant_isolation_between_organizations(app_session: AsyncSession, tmp_path: Path):
    async def _run_test():
        settings.local_upload_path = tmp_path / "uploads"
        auth_service = AuthService(app_session)
        user_a = await auth_service.register_user(
            email="tenant-a@example.com",
            first_name="Tenant",
            last_name="A",
            password="SecurePass456!",
            organization_name="Tenant Org A",
        )
        user_b = await auth_service.register_user(
            email="tenant-b@example.com",
            first_name="Tenant",
            last_name="B",
            password="SecurePass456!",
            organization_name="Tenant Org B",
        )

        service_a = FileService(app_session, organization_id=user_a.organization_id)
        service_b = FileService(app_session, organization_id=user_b.organization_id)

        file_a = await service_a.upload_file(make_upload_file("a-only.pdf", b"org a data", "application/pdf"), user_a.id)

        assert await service_b.get_file(file_a.id) is None
        assert file_a.id not in {f.id for f in await service_b.list_files()}

    asyncio.run(_run_test())


def test_public_file_visibility(app_session: AsyncSession, tmp_path: Path):
    async def _run_test():
        settings.local_upload_path = tmp_path / "uploads"
        auth_service = AuthService(app_session)
        user = await auth_service.register_user(
            email="visibility@example.com",
            first_name="Vis",
            last_name="Tester",
            password="SecurePass456!",
            organization_name="Visibility Org",
        )
        file_service = FileService(app_session, organization_id=user.organization_id)

        public_file = await file_service.upload_file(
            make_upload_file("public.pdf", b"public contents", "application/pdf"),
            user.id,
            visibility=FileVisibility.public,
        )
        assert public_file.visibility == FileVisibility.public

    asyncio.run(_run_test())


def test_search_finds_files_and_folders(app_session: AsyncSession, tmp_path: Path):
    async def _run_test():
        settings.local_upload_path = tmp_path / "uploads"
        auth_service = AuthService(app_session)
        user = await auth_service.register_user(
            email="search@example.com",
            first_name="Search",
            last_name="Tester",
            password="SecurePass456!",
            organization_name="Search Org",
        )
        file_service = FileService(app_session, organization_id=user.organization_id)

        await file_service.create_folder("Invoices 2026", created_by=user.id)
        await file_service.upload_file(make_upload_file("invoice-january.pdf", b"data", "application/pdf"), user.id)

        results = await file_service.search("invoice")
        assert len(results["files"]) == 1
        assert len(results["folders"]) == 1

    asyncio.run(_run_test())

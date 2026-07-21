import asyncio
from datetime import datetime, timedelta

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.db import Base
from app.services.audit_service import AuditService
from app.services.auth_service import AuthService


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


def test_audit_log_created_and_searchable(app_session: AsyncSession):
    async def _run_test():
        auth_service = AuthService(app_session)
        user = await auth_service.register_user(
            email="auditor@example.com",
            first_name="Audit",
            last_name="Tester",
            password="SecurePass456!",
            organization_name="Audit Org",
        )

        audit_service = AuditService(app_session, organization_id=user.organization_id)
        await audit_service.log(action="create", module="files", entity="File", entity_id="file-1", user_id=user.id, after={"name": "a.pdf"})
        await audit_service.log(action="delete", module="files", entity="File", entity_id="file-1", user_id=user.id, before={"name": "a.pdf"})
        await audit_service.log(action="login", module="auth", entity="User", entity_id=user.id, user_id=user.id)

        items, total = await audit_service.search()
        assert total == 3
        assert len(items) == 3
        assert items[0].action == "login"  # most recent first

        items, total = await audit_service.search(module="files", action="delete")
        assert total == 1
        assert items[0].entity_id == "file-1"

    asyncio.run(_run_test())


def test_audit_log_tenant_isolation(app_session: AsyncSession):
    async def _run_test():
        auth_service = AuthService(app_session)
        user_a = await auth_service.register_user(
            email="tenant-a@example.com", first_name="A", last_name="Org",
            password="SecurePass456!", organization_name="Audit Tenant A",
        )
        user_b = await auth_service.register_user(
            email="tenant-b@example.com", first_name="B", last_name="Org",
            password="SecurePass456!", organization_name="Audit Tenant B",
        )

        await AuditService(app_session, organization_id=user_a.organization_id).log(
            action="create", module="files", entity="File", user_id=user_a.id
        )

        items_a, total_a = await AuditService(app_session, organization_id=user_a.organization_id).search()
        items_b, total_b = await AuditService(app_session, organization_id=user_b.organization_id).search()

        assert total_a == 1
        assert total_b == 0
        assert items_b == []

    asyncio.run(_run_test())


def test_audit_log_date_range_filter(app_session: AsyncSession):
    async def _run_test():
        auth_service = AuthService(app_session)
        user = await auth_service.register_user(
            email="dates@example.com", first_name="Date", last_name="Tester",
            password="SecurePass456!", organization_name="Audit Dates Org",
        )
        audit_service = AuditService(app_session, organization_id=user.organization_id)
        await audit_service.log(action="create", module="files", user_id=user.id)

        future_start = datetime.utcnow() + timedelta(days=1)
        items, total = await audit_service.search(date_from=future_start)
        assert total == 0

        past_start = datetime.utcnow() - timedelta(days=1)
        items, total = await audit_service.search(date_from=past_start)
        assert total == 1

    asyncio.run(_run_test())


def test_audit_log_export_csv(app_session: AsyncSession):
    async def _run_test():
        auth_service = AuthService(app_session)
        user = await auth_service.register_user(
            email="export@example.com", first_name="Export", last_name="Tester",
            password="SecurePass456!", organization_name="Audit Export Org",
        )
        audit_service = AuditService(app_session, organization_id=user.organization_id)
        await audit_service.log(action="create", module="files", entity="File", entity_id="f-1", user_id=user.id)

        csv_text = await audit_service.export_csv()
        lines = csv_text.strip().splitlines()
        assert lines[0].startswith("id,created_at,user_id,action,module")
        assert "create" in lines[1]
        assert "files" in lines[1]

    asyncio.run(_run_test())


def test_audit_log_never_raises_on_failure(app_session: AsyncSession):
    async def _run_test():
        audit_service = AuditService(app_session, organization_id=None)
        # No organization_id and a required NOT NULL "action" omission would normally
        # violate the schema; the service should swallow the failure, not raise.
        result = await audit_service.log(action="create", module="files")
        assert result is None or result.organization_id is None

    asyncio.run(_run_test())

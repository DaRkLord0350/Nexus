import asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from app.db import Base
from app.services.auth_service import AuthService
from app.services.dashboard_service import DashboardService


async def _create_session(database_url: str) -> AsyncSession:
    engine = create_async_engine(database_url, future=True)
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    async_session = async_sessionmaker(engine, expire_on_commit=False)
    return async_session()


def test_dashboard_service_returns_metrics():
    async def run_test():
        session = await _create_session("sqlite+aiosqlite:///:memory:")
        try:
            auth_service = AuthService(session)
            user = await auth_service.register_user(
                email="dashboard-owner@example.com",
                first_name="Dashboard",
                last_name="Owner",
                password="StrongPass123!",
                organization_name="CommerceOS Dashboard",
            )
            dashboard_service = DashboardService(session, organization_id=user.organization_id)
            dashboard = await dashboard_service.get_dashboard()

            assert dashboard["organization"]["name"] == "CommerceOS Dashboard"
            assert any(metric["id"] == "customers" for metric in dashboard["metrics"])
            assert dashboard["metrics"][0]["value"] == 1
            assert isinstance(dashboard["recent_activity"], list)
            assert dashboard["summary"]["generated_at"] is not None
        finally:
            await session.close()

    asyncio.run(run_test())

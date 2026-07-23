import asyncio

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.db import Base
from app.schemas.shipping_rule import ShippingRuleCreateRequest, ShippingRuleEvaluateRequest
from app.services.auth_service import AuthService
from app.services.shipping_rule_service import ShippingRuleService


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


async def _register_org(session, email="owner@example.com", org_name="Rule Test Org"):
    auth_service = AuthService(session)
    return await auth_service.register_user(
        email=email, first_name="Ada", last_name="Lovelace", password="SecurePass456!", organization_name=org_name,
    )


def test_weight_rule_assigns_preferred_provider(app_session: AsyncSession):
    async def _run():
        user = await _register_org(app_session)
        service = ShippingRuleService(app_session, organization_id=user.organization_id)
        await service.create_rule(ShippingRuleCreateRequest(
            name="Heavy packages go via freight", condition_type="weight_greater_than", condition_value="5",
            action_type="assign_provider", action_value="freight-provider-id",
        ), created_by=user.id)

        result = await service.evaluate(ShippingRuleEvaluateRequest(weight=7.5))
        assert result["preferred_provider_id"] == "freight-provider-id"

        result_light = await service.evaluate(ShippingRuleEvaluateRequest(weight=2.0))
        assert result_light["preferred_provider_id"] is None

    asyncio.run(_run())


def test_cod_rule_excludes_provider(app_session: AsyncSession):
    async def _run():
        user = await _register_org(app_session)
        service = ShippingRuleService(app_session, organization_id=user.organization_id)
        await service.create_rule(ShippingRuleCreateRequest(
            name="No COD via provider X", condition_type="is_cod", condition_value="true",
            action_type="exclude_provider", action_value="no-cod-provider-id",
        ), created_by=user.id)

        result = await service.evaluate(ShippingRuleEvaluateRequest(is_cod=True))
        assert "no-cod-provider-id" in result["excluded_provider_ids"]

        result_no_cod = await service.evaluate(ShippingRuleEvaluateRequest(is_cod=False))
        assert result_no_cod["excluded_provider_ids"] == []

    asyncio.run(_run())


def test_state_rule_prefers_warehouse(app_session: AsyncSession):
    async def _run():
        user = await _register_org(app_session)
        service = ShippingRuleService(app_session, organization_id=user.organization_id)
        await service.create_rule(ShippingRuleCreateRequest(
            name="California orders from West warehouse", condition_type="destination_state", condition_value="CA",
            action_type="prefer_warehouse", action_value="west-warehouse-id",
        ), created_by=user.id)

        result = await service.evaluate(ShippingRuleEvaluateRequest(destination_state="CA"))
        assert result["preferred_warehouse_id"] == "west-warehouse-id"

        result_other_state = await service.evaluate(ShippingRuleEvaluateRequest(destination_state="NY"))
        assert result_other_state["preferred_warehouse_id"] is None

    asyncio.run(_run())


def test_multiple_exclude_rules_accumulate(app_session: AsyncSession):
    async def _run():
        user = await _register_org(app_session)
        service = ShippingRuleService(app_session, organization_id=user.organization_id)
        await service.create_rule(ShippingRuleCreateRequest(
            name="Exclude A on COD", condition_type="is_cod", condition_value="true", action_type="exclude_provider", action_value="provider-a",
        ), created_by=user.id)
        await service.create_rule(ShippingRuleCreateRequest(
            name="Exclude B on COD", condition_type="is_cod", condition_value="true", action_type="exclude_provider", action_value="provider-b",
        ), created_by=user.id)

        result = await service.evaluate(ShippingRuleEvaluateRequest(is_cod=True))
        assert set(result["excluded_provider_ids"]) == {"provider-a", "provider-b"}
        assert len(result["matched_rule_ids"]) == 2

    asyncio.run(_run())


def test_inactive_rule_is_ignored(app_session: AsyncSession):
    async def _run():
        user = await _register_org(app_session)
        service = ShippingRuleService(app_session, organization_id=user.organization_id)
        await service.create_rule(ShippingRuleCreateRequest(
            name="Disabled rule", is_active=False, condition_type="is_cod", condition_value="true",
            action_type="exclude_provider", action_value="provider-x",
        ), created_by=user.id)

        result = await service.evaluate(ShippingRuleEvaluateRequest(is_cod=True))
        assert result["excluded_provider_ids"] == []

    asyncio.run(_run())


def test_update_and_delete_rule(app_session: AsyncSession):
    async def _run():
        user = await _register_org(app_session)
        service = ShippingRuleService(app_session, organization_id=user.organization_id)
        rule = await service.create_rule(ShippingRuleCreateRequest(
            name="Rule", condition_type="is_cod", condition_value="true", action_type="exclude_provider", action_value="provider-x",
        ), created_by=user.id)

        from app.schemas.shipping_rule import ShippingRuleUpdateRequest
        updated = await service.update_rule(rule.id, ShippingRuleUpdateRequest(is_active=False))
        assert updated.is_active is False

        await service.delete_rule(rule.id)
        assert await service.get_rule(rule.id) is None

    asyncio.run(_run())


def test_tenant_isolation(app_session: AsyncSession):
    async def _run():
        user_a = await _register_org(app_session, email="a@example.com", org_name="Org A")
        user_b = await _register_org(app_session, email="b@example.com", org_name="Org B")

        service_a = ShippingRuleService(app_session, organization_id=user_a.organization_id)
        service_b = ShippingRuleService(app_session, organization_id=user_b.organization_id)
        rule = await service_a.create_rule(ShippingRuleCreateRequest(
            name="A only rule", condition_type="is_cod", condition_value="true", action_type="exclude_provider", action_value="provider-x",
        ), created_by=user_a.id)

        assert await service_b.get_rule(rule.id) is None
        result_b = await service_b.evaluate(ShippingRuleEvaluateRequest(is_cod=True))
        assert result_b["excluded_provider_ids"] == []

    asyncio.run(_run())


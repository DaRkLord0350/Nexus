import asyncio

import pytest
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.db import Base
from app.models.inventory_transaction import InventoryTransactionType
from app.schemas.inventory import InventoryUpdateRequest
from app.schemas.product import ProductCreateRequest
from app.schemas.reorder_rule import ReorderRuleCreateRequest
from app.schemas.warehouse import WarehouseCreateRequest
from app.services.auth_service import AuthService
from app.services.inventory_service import InventoryService
from app.services.notification_service import NotificationService
from app.services.product_service import ProductService
from app.services.reorder_rule_service import ReorderRuleService
from app.services.stock_movement_service import StockMovementService
from app.services.warehouse_service import WarehouseService


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


async def _register_org(session, email="owner@example.com", org_name="Stock Test Org"):
    auth_service = AuthService(session)
    return await auth_service.register_user(
        email=email, first_name="Ada", last_name="Lovelace", password="SecurePass456!", organization_name=org_name,
    )


async def _setup_product_and_warehouse(session, org_id, user_id):
    product_service = ProductService(session, organization_id=org_id)
    product = await product_service.create_product(ProductCreateRequest(name="Widget", sku="WID-1"), created_by=user_id)

    warehouse_service = WarehouseService(session, organization_id=org_id)
    warehouse = await warehouse_service.create_warehouse(WarehouseCreateRequest(name="Main", code="MAIN"), created_by=user_id)

    return product, warehouse


def test_apply_movement_creates_inventory_and_transaction(app_session: AsyncSession):
    async def _run():
        user = await _register_org(app_session)
        product, warehouse = await _setup_product_and_warehouse(app_session, user.organization_id, user.id)
        movement_service = StockMovementService(app_session, organization_id=user.organization_id)

        transaction = await movement_service.apply_movement(
            product_id=product.id,
            variant_id=None,
            warehouse_id=warehouse.id,
            transaction_type=InventoryTransactionType.receive,
            quantity_delta=100,
            reference_type="goods_receipt",
            reference_id="test-ref",
            user_id=user.id,
        )
        assert transaction.quantity == 100
        assert transaction.quantity_before == 0
        assert transaction.quantity_after == 100

        inventory_service = InventoryService(app_session, organization_id=user.organization_id)
        inventory = await inventory_service.get_inventory(transaction.inventory_id)
        assert inventory.quantity_available == 100

    asyncio.run(_run())


def test_apply_movement_accumulates_on_same_grain(app_session: AsyncSession):
    async def _run():
        user = await _register_org(app_session)
        product, warehouse = await _setup_product_and_warehouse(app_session, user.organization_id, user.id)
        movement_service = StockMovementService(app_session, organization_id=user.organization_id)

        await movement_service.apply_movement(
            product_id=product.id, variant_id=None, warehouse_id=warehouse.id,
            transaction_type=InventoryTransactionType.receive, quantity_delta=50,
        )
        second = await movement_service.apply_movement(
            product_id=product.id, variant_id=None, warehouse_id=warehouse.id,
            transaction_type=InventoryTransactionType.sale, quantity_delta=-20,
        )
        assert second.quantity_before == 50
        assert second.quantity_after == 30

    asyncio.run(_run())


def test_negative_quantity_rejected(app_session: AsyncSession):
    async def _run():
        user = await _register_org(app_session)
        product, warehouse = await _setup_product_and_warehouse(app_session, user.organization_id, user.id)
        movement_service = StockMovementService(app_session, organization_id=user.organization_id)

        with pytest.raises(HTTPException) as exc_info:
            await movement_service.apply_movement(
                product_id=product.id, variant_id=None, warehouse_id=warehouse.id,
                transaction_type=InventoryTransactionType.sale, quantity_delta=-10,
            )
        assert exc_info.value.status_code == 400

    asyncio.run(_run())


def test_negative_quantity_allowed_when_flagged(app_session: AsyncSession):
    async def _run():
        user = await _register_org(app_session)
        product, warehouse = await _setup_product_and_warehouse(app_session, user.organization_id, user.id)
        movement_service = StockMovementService(app_session, organization_id=user.organization_id)

        transaction = await movement_service.apply_movement(
            product_id=product.id, variant_id=None, warehouse_id=warehouse.id,
            transaction_type=InventoryTransactionType.adjustment, quantity_delta=-10, allow_negative=True,
        )
        assert transaction.quantity_after == -10

    asyncio.run(_run())


def test_low_stock_notification_fires_once_within_cooldown(app_session: AsyncSession):
    async def _run():
        user = await _register_org(app_session)
        product, warehouse = await _setup_product_and_warehouse(app_session, user.organization_id, user.id)
        movement_service = StockMovementService(app_session, organization_id=user.organization_id)

        await movement_service.apply_movement(
            product_id=product.id, variant_id=None, warehouse_id=warehouse.id,
            transaction_type=InventoryTransactionType.receive, quantity_delta=20,
        )

        inventory_service = InventoryService(app_session, organization_id=user.organization_id)
        inventory, _ = await inventory_service.list_inventory(warehouse_id=warehouse.id)
        inventory = inventory[0]
        await inventory_service.update_inventory(inventory.id, InventoryUpdateRequest(reorder_point=15))

        await movement_service.apply_movement(
            product_id=product.id, variant_id=None, warehouse_id=warehouse.id,
            transaction_type=InventoryTransactionType.sale, quantity_delta=-10,
        )

        notification_service = NotificationService(app_session, organization_id=user.organization_id)
        notifications = await notification_service.list_notifications(user.id, limit=50)
        low_stock_notifications = [n for n in notifications if n.title == "Low stock alert"]
        assert len(low_stock_notifications) == 1

        refreshed = await inventory_service.get_inventory(inventory.id)
        assert refreshed.low_stock_notified_at is not None

        # A second decrease within the cooldown window should not notify again.
        await movement_service.apply_movement(
            product_id=product.id, variant_id=None, warehouse_id=warehouse.id,
            transaction_type=InventoryTransactionType.sale, quantity_delta=-1,
        )
        notifications_after = await notification_service.list_notifications(user.id, limit=50)
        low_stock_notifications_after = [n for n in notifications_after if n.title == "Low stock alert"]
        assert len(low_stock_notifications_after) == 1

    asyncio.run(_run())


def test_tenant_isolation(app_session: AsyncSession):
    async def _run():
        user_a = await _register_org(app_session, email="a@example.com", org_name="Org A")
        user_b = await _register_org(app_session, email="b@example.com", org_name="Org B")
        product_a, warehouse_a = await _setup_product_and_warehouse(app_session, user_a.organization_id, user_a.id)

        movement_service_a = StockMovementService(app_session, organization_id=user_a.organization_id)
        transaction = await movement_service_a.apply_movement(
            product_id=product_a.id, variant_id=None, warehouse_id=warehouse_a.id,
            transaction_type=InventoryTransactionType.receive, quantity_delta=10,
        )

        inventory_service_b = InventoryService(app_session, organization_id=user_b.organization_id)
        assert await inventory_service_b.get_inventory(transaction.inventory_id) is None

    asyncio.run(_run())


def test_low_stock_notification_includes_reorder_rule_suggestion(app_session: AsyncSession):
    async def _run():
        user = await _register_org(app_session)
        product, warehouse = await _setup_product_and_warehouse(app_session, user.organization_id, user.id)
        movement_service = StockMovementService(app_session, organization_id=user.organization_id)

        await movement_service.apply_movement(
            product_id=product.id, variant_id=None, warehouse_id=warehouse.id,
            transaction_type=InventoryTransactionType.receive, quantity_delta=20,
        )

        inventory_service = InventoryService(app_session, organization_id=user.organization_id)
        items, _ = await inventory_service.list_inventory(warehouse_id=warehouse.id)
        inventory = items[0]
        await inventory_service.update_inventory(inventory.id, InventoryUpdateRequest(reorder_point=15))

        reorder_service = ReorderRuleService(app_session, organization_id=user.organization_id)
        rule = await reorder_service.create_rule(ReorderRuleCreateRequest(
            product_id=product.id, warehouse_id=warehouse.id, minimum_stock=10, reorder_quantity=100, supplier_name="Acme Supplies",
        ))

        await movement_service.apply_movement(
            product_id=product.id, variant_id=None, warehouse_id=warehouse.id,
            transaction_type=InventoryTransactionType.sale, quantity_delta=-10,
        )

        notification_service = NotificationService(app_session, organization_id=user.organization_id)
        notifications = await notification_service.list_notifications(user.id, limit=50)
        low_stock_notifications = [n for n in notifications if n.title == "Low stock alert"]
        assert len(low_stock_notifications) == 1
        assert low_stock_notifications[0].payload["suggested_reorder_quantity"] == 100
        assert low_stock_notifications[0].payload["supplier_name"] == "Acme Supplies"

        refreshed_rule = await reorder_service.get_rule(rule.id)
        assert refreshed_rule.last_triggered_at is not None

    asyncio.run(_run())

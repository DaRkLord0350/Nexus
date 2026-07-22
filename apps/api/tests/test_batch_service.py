import asyncio

import pytest
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.db import Base
from app.schemas.batch import BatchCreateRequest, BatchUpdateRequest
from app.schemas.product import ProductCreateRequest
from app.schemas.warehouse import WarehouseCreateRequest
from app.services.auth_service import AuthService
from app.services.batch_service import BatchService
from app.services.product_service import ProductService
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


async def _register_org(session, email="owner@example.com", org_name="Batch Test Org"):
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


def test_create_batch(app_session: AsyncSession):
    async def _run():
        user = await _register_org(app_session)
        product, warehouse = await _setup_product_and_warehouse(app_session, user.organization_id, user.id)
        service = BatchService(app_session, organization_id=user.organization_id)

        batch = await service.create_batch(BatchCreateRequest(
            product_id=product.id, warehouse_id=warehouse.id, batch_number="LOT-001", received_quantity=100,
        ))
        assert batch.received_quantity == 100
        assert batch.remaining_quantity == 100
        assert batch.status.value == "active"
        assert batch.inventory_id is not None

    asyncio.run(_run())


def test_duplicate_batch_number_rejected(app_session: AsyncSession):
    async def _run():
        user = await _register_org(app_session)
        product, warehouse = await _setup_product_and_warehouse(app_session, user.organization_id, user.id)
        service = BatchService(app_session, organization_id=user.organization_id)
        await service.create_batch(BatchCreateRequest(product_id=product.id, warehouse_id=warehouse.id, batch_number="LOT-001"))
        with pytest.raises(HTTPException) as exc_info:
            await service.create_batch(BatchCreateRequest(product_id=product.id, warehouse_id=warehouse.id, batch_number="LOT-001"))
        assert exc_info.value.status_code == 400

    asyncio.run(_run())


def test_get_or_create_batch_accumulates(app_session: AsyncSession):
    async def _run():
        user = await _register_org(app_session)
        product, warehouse = await _setup_product_and_warehouse(app_session, user.organization_id, user.id)
        service = BatchService(app_session, organization_id=user.organization_id)

        from app.repositories.inventory_repository import InventoryRepository
        inventory_repo = InventoryRepository(app_session, organization_id=user.organization_id)
        inventory = await inventory_repo.get_or_create_for_update(product.id, None, warehouse.id)
        await app_session.commit()

        batch1 = await service.get_or_create_batch(inventory.id, product.id, None, warehouse.id, "LOT-A", 50)
        await app_session.commit()
        assert batch1.remaining_quantity == 50

        batch2 = await service.get_or_create_batch(inventory.id, product.id, None, warehouse.id, "LOT-A", 30)
        await app_session.commit()
        assert batch2.id == batch1.id
        assert batch2.remaining_quantity == 80
        assert batch2.received_quantity == 80

    asyncio.run(_run())


def test_update_and_delete_batch(app_session: AsyncSession):
    async def _run():
        user = await _register_org(app_session)
        product, warehouse = await _setup_product_and_warehouse(app_session, user.organization_id, user.id)
        service = BatchService(app_session, organization_id=user.organization_id)
        batch = await service.create_batch(BatchCreateRequest(product_id=product.id, warehouse_id=warehouse.id, batch_number="LOT-001", received_quantity=10))

        updated = await service.update_batch(batch.id, BatchUpdateRequest(status="quarantined", remaining_quantity=5))
        assert updated.status.value == "quarantined"
        assert updated.remaining_quantity == 5

        await service.delete_batch(batch.id)
        assert await service.get_batch(batch.id) is None

    asyncio.run(_run())


def test_list_batches_filters(app_session: AsyncSession):
    async def _run():
        user = await _register_org(app_session)
        product, warehouse = await _setup_product_and_warehouse(app_session, user.organization_id, user.id)
        service = BatchService(app_session, organization_id=user.organization_id)
        await service.create_batch(BatchCreateRequest(product_id=product.id, warehouse_id=warehouse.id, batch_number="LOT-A"))
        await service.create_batch(BatchCreateRequest(product_id=product.id, warehouse_id=warehouse.id, batch_number="LOT-B"))

        items, total = await service.list_batches(warehouse_id=warehouse.id)
        assert total == 2
        assert len(items) == 2

    asyncio.run(_run())


def test_tenant_isolation(app_session: AsyncSession):
    async def _run():
        user_a = await _register_org(app_session, email="a@example.com", org_name="Org A")
        user_b = await _register_org(app_session, email="b@example.com", org_name="Org B")
        product_a, warehouse_a = await _setup_product_and_warehouse(app_session, user_a.organization_id, user_a.id)

        service_a = BatchService(app_session, organization_id=user_a.organization_id)
        service_b = BatchService(app_session, organization_id=user_b.organization_id)
        batch = await service_a.create_batch(BatchCreateRequest(product_id=product_a.id, warehouse_id=warehouse_a.id, batch_number="LOT-A"))

        assert await service_b.get_batch(batch.id) is None

    asyncio.run(_run())

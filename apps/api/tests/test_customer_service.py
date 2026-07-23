import asyncio

import pytest
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.db import Base
from app.schemas.address import AddressCreateRequest, AddressUpdateRequest
from app.schemas.customer import CustomerCreateRequest, CustomerUpdateRequest
from app.services.auth_service import AuthService
from app.services.customer_auth_service import CustomerAuthService
from app.services.customer_service import CustomerService


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


async def _register_org(session, email="owner@example.com", org_name="Customer Test Org"):
    auth_service = AuthService(session)
    return await auth_service.register_user(
        email=email, first_name="Ada", last_name="Lovelace", password="SecurePass456!", organization_name=org_name,
    )


def test_create_customer(app_session: AsyncSession):
    async def _run():
        user = await _register_org(app_session)
        service = CustomerService(app_session, organization_id=user.organization_id)

        customer = await service.create_customer(
            CustomerCreateRequest(email="shopper@example.com", first_name="Sam", last_name="Shopper"),
            created_by=user.id,
        )
        assert customer.email == "shopper@example.com"
        assert customer.is_guest is True
        assert customer.hashed_password is None

    asyncio.run(_run())


def test_duplicate_email_rejected(app_session: AsyncSession):
    async def _run():
        user = await _register_org(app_session)
        service = CustomerService(app_session, organization_id=user.organization_id)
        await service.create_customer(CustomerCreateRequest(email="dup@example.com", first_name="A", last_name="B"), created_by=user.id)

        with pytest.raises(HTTPException) as exc_info:
            await service.create_customer(CustomerCreateRequest(email="dup@example.com", first_name="C", last_name="D"), created_by=user.id)
        assert exc_info.value.status_code == 400

    asyncio.run(_run())


def test_update_and_soft_delete_customer(app_session: AsyncSession):
    async def _run():
        user = await _register_org(app_session)
        service = CustomerService(app_session, organization_id=user.organization_id)
        customer = await service.create_customer(CustomerCreateRequest(email="edit@example.com", first_name="A", last_name="B"), created_by=user.id)

        updated = await service.update_customer(customer.id, CustomerUpdateRequest(first_name="Updated"))
        assert updated.first_name == "Updated"

        await service.delete_customer(customer.id)
        assert await service.get_customer(customer.id) is None

        restored = await service.restore_customer(customer.id)
        assert restored is not None
        assert restored.deleted_at is None

    asyncio.run(_run())


def test_add_address_manages_default_flag(app_session: AsyncSession):
    async def _run():
        user = await _register_org(app_session)
        service = CustomerService(app_session, organization_id=user.organization_id)
        customer = await service.create_customer(CustomerCreateRequest(email="addr@example.com", first_name="A", last_name="B"), created_by=user.id)

        first = await service.add_address(customer.id, AddressCreateRequest(
            first_name="A", last_name="B", line1="123 Main St", city="Metropolis", country="us", is_default=True,
        ))
        assert first.is_default is True
        assert first.country == "US"

        second = await service.add_address(customer.id, AddressCreateRequest(
            first_name="A", last_name="B", line1="456 Other St", city="Gotham", country="us", is_default=True,
        ))
        assert second.is_default is True

        items, total = await service.list_addresses(customer.id)
        assert total == 2
        refreshed_first = next(a for a in items if a.id == first.id)
        assert refreshed_first.is_default is False

    asyncio.run(_run())


def test_update_address_not_found_raises(app_session: AsyncSession):
    async def _run():
        user = await _register_org(app_session)
        service = CustomerService(app_session, organization_id=user.organization_id)
        customer = await service.create_customer(CustomerCreateRequest(email="missing@example.com", first_name="A", last_name="B"), created_by=user.id)

        with pytest.raises(HTTPException) as exc_info:
            await service.update_address(customer.id, "nonexistent-id", AddressUpdateRequest(city="New City"))
        assert exc_info.value.status_code == 404

    asyncio.run(_run())


def test_customer_auth_register_and_login(app_session: AsyncSession):
    async def _run():
        user = await _register_org(app_session)
        auth_service = CustomerAuthService(app_session, user.organization_id)

        customer = await auth_service.register(
            email="auth@example.com", first_name="A", last_name="B", password="StrongPass1!", phone=None, accepts_marketing=False,
        )
        assert customer.is_guest is False

        with pytest.raises(HTTPException) as exc_info:
            await auth_service.authenticate("auth@example.com", "WrongPass")
        assert exc_info.value.status_code == 401

        authenticated, token = await auth_service.login("auth@example.com", "StrongPass1!")
        assert authenticated.id == customer.id
        assert token

    asyncio.run(_run())


def test_guest_can_register_later(app_session: AsyncSession):
    async def _run():
        user = await _register_org(app_session)
        auth_service = CustomerAuthService(app_session, user.organization_id)

        guest = await auth_service.get_or_create_guest(email="guest@example.com", first_name="G", last_name="H")
        assert guest.is_guest is True

        registered = await auth_service.register(
            email="guest@example.com", first_name="G", last_name="H", password="AnotherPass1!", phone=None, accepts_marketing=True,
        )
        assert registered.id == guest.id
        assert registered.is_guest is False

    asyncio.run(_run())


def test_tenant_isolation(app_session: AsyncSession):
    async def _run():
        user_a = await _register_org(app_session, email="a@example.com", org_name="Org A")
        user_b = await _register_org(app_session, email="b@example.com", org_name="Org B")

        service_a = CustomerService(app_session, organization_id=user_a.organization_id)
        service_b = CustomerService(app_session, organization_id=user_b.organization_id)
        customer = await service_a.create_customer(CustomerCreateRequest(email="iso@example.com", first_name="A", last_name="B"), created_by=user_a.id)

        assert await service_b.get_customer(customer.id) is None

    asyncio.run(_run())


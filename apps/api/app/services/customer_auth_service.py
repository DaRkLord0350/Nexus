from datetime import datetime, timedelta

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.customer import Customer
from app.repositories.customer_repository import CustomerRepository
from app.utils.security import create_access_token, hash_password, verify_password

CUSTOMER_TOKEN_EXPIRE_DAYS = 14


class CustomerAuthService:
    """Storefront-facing authentication for Customer accounts.

    Deliberately independent of AuthService/User: customers are not staff
    and must never gain RBAC permissions or organization-management access.
    Kept lightweight (no refresh-token/session revocation table) since this
    is a first pass at storefront auth."""

    def __init__(self, session: AsyncSession, organization_id: str):
        self.session = session
        self.organization_id = organization_id
        self.repo = CustomerRepository(session, organization_id)

    async def register(self, email: str, first_name: str, last_name: str, password: str, phone: str | None, accepts_marketing: bool) -> Customer:
        existing = await self.repo.get_by_email(email)
        if existing and not existing.is_guest:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email is already registered.")

        if existing and existing.is_guest:
            existing.hashed_password = hash_password(password)
            existing.first_name = first_name
            existing.last_name = last_name
            existing.phone = phone or existing.phone
            existing.accepts_marketing = accepts_marketing
            existing.is_guest = False
            return await self.repo.save(existing)

        customer = Customer(
            organization_id=self.organization_id,
            email=email,
            first_name=first_name,
            last_name=last_name,
            phone=phone,
            hashed_password=hash_password(password),
            is_guest=False,
            accepts_marketing=accepts_marketing,
        )
        return await self.repo.create(customer)

    async def get_or_create_guest(self, email: str, first_name: str, last_name: str, phone: str | None = None) -> Customer:
        existing = await self.repo.get_by_email(email)
        if existing:
            return existing
        customer = Customer(
            organization_id=self.organization_id,
            email=email,
            first_name=first_name,
            last_name=last_name,
            phone=phone,
            is_guest=True,
        )
        return await self.repo.create(customer)

    async def authenticate(self, email: str, password: str) -> Customer:
        customer = await self.repo.get_by_email(email)
        if not customer or customer.is_guest or not customer.hashed_password or not verify_password(password, customer.hashed_password):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials.")
        if not customer.is_active:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is disabled.")

        customer.last_login_at = datetime.utcnow()
        return await self.repo.save(customer)

    def create_token(self, customer: Customer) -> str:
        return create_access_token(
            subject=customer.id,
            expires_delta=timedelta(days=CUSTOMER_TOKEN_EXPIRE_DAYS),
            additional_claims={"typ": "customer", "oid": customer.organization_id},
        )

    async def login(self, email: str, password: str) -> tuple[Customer, str]:
        customer = await self.authenticate(email, password)
        return customer, self.create_token(customer)

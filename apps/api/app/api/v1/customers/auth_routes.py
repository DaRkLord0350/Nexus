from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_customer, get_db
from app.schemas.customer import CustomerItem, CustomerLoginRequest, CustomerRegisterRequest, CustomerTokenResponse
from app.services.customer_auth_service import CustomerAuthService

router = APIRouter(prefix="/customers/auth", tags=["customers-auth"])


@router.post("/register", response_model=CustomerTokenResponse, status_code=status.HTTP_201_CREATED)
async def register_customer(data: CustomerRegisterRequest, db: AsyncSession = Depends(get_db)):
    service = CustomerAuthService(db, data.organization_id)
    customer = await service.register(
        email=data.email,
        first_name=data.first_name,
        last_name=data.last_name,
        password=data.password,
        phone=data.phone,
        accepts_marketing=data.accepts_marketing,
    )
    token = service.create_token(customer)
    return {"access_token": token, "customer": customer}


@router.post("/login", response_model=CustomerTokenResponse)
async def login_customer(data: CustomerLoginRequest, db: AsyncSession = Depends(get_db)):
    service = CustomerAuthService(db, data.organization_id)
    customer, token = await service.login(data.email, data.password)
    return {"access_token": token, "customer": customer}


@router.get("/me", response_model=CustomerItem)
async def get_current_customer_profile(current_customer=Depends(get_current_customer)):
    return current_customer

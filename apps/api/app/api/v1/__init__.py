from fastapi import APIRouter

from app.api.v1.audit.routes import router as audit_router
from app.api.v1.auth.routes import router as auth_router
from app.api.v1.dashboard.routes import router as dashboard_router
from app.api.v1.files.routes import router as files_router
from app.api.v1.notifications.routes import router as notifications_router
from app.api.v1.organizations.routes import router as organizations_router
from app.api.v1.rbac.routes import router as rbac_router

api_router = APIRouter()
api_router.include_router(audit_router)
api_router.include_router(auth_router)
api_router.include_router(dashboard_router)
api_router.include_router(files_router)
api_router.include_router(notifications_router)
api_router.include_router(organizations_router)
api_router.include_router(rbac_router)

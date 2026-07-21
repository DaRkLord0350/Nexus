from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.health.routes import router as health_router
from app.api.v1 import api_router
from app.core.config import settings
from app.core.logging import configure_logging
from app.middleware.audit import AuditContextMiddleware
from app.middleware.rate_limiter import RateLimiterMiddleware
from app.middleware.security_headers import HTTPSRedirectMiddleware, SecurityHeadersMiddleware
from app.middleware.tenant import TenantMiddleware


def create_application() -> FastAPI:
    configure_logging()

    application = FastAPI(
        title=settings.project_name,
        version="1.0.0",
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        openapi_url="/api/openapi.json",
    )

    application.add_middleware(RateLimiterMiddleware)
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    application.add_middleware(TenantMiddleware)
    application.add_middleware(SecurityHeadersMiddleware)
    application.add_middleware(HTTPSRedirectMiddleware)
    # Outermost: the request id must exist before any other middleware runs
    # so every downstream log line (including from CORS/rate-limit rejections)
    # can be correlated.
    application.add_middleware(AuditContextMiddleware)

    application.include_router(health_router)
    application.include_router(api_router, prefix="/api/v1")

    return application


app = create_application()

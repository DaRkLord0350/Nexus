from fastapi import APIRouter

from app.api.v1.audit.routes import router as audit_router
from app.api.v1.auth.routes import router as auth_router
from app.api.v1.catalog.attributes.routes import router as catalog_attributes_router
from app.api.v1.catalog.brands.routes import router as catalog_brands_router
from app.api.v1.catalog.categories.routes import router as catalog_categories_router
from app.api.v1.catalog.channels.routes import router as catalog_channels_router
from app.api.v1.catalog.collections.routes import router as catalog_collections_router
from app.api.v1.catalog.coupons.routes import router as catalog_coupons_router
from app.api.v1.catalog.custom_fields.routes import router as catalog_custom_fields_router
from app.api.v1.catalog.media.routes import router as catalog_media_router
from app.api.v1.catalog.pricing.routes import router as catalog_pricing_router
from app.api.v1.catalog.products.routes import router as catalog_products_router
from app.api.v1.catalog.product_channels.routes import router as catalog_product_channels_router
from app.api.v1.catalog.product_types.routes import router as catalog_product_types_router
from app.api.v1.catalog.seo.routes import router as catalog_seo_router
from app.api.v1.catalog.tags.routes import router as catalog_tags_router
from app.api.v1.catalog.taxes.routes import router as catalog_taxes_router
from app.api.v1.catalog.variants.routes import router as catalog_variants_router
from app.api.v1.dashboard.routes import router as dashboard_router
from app.api.v1.files.routes import router as files_router
from app.api.v1.notifications.routes import router as notifications_router
from app.api.v1.organizations.routes import router as organizations_router
from app.api.v1.rbac.routes import router as rbac_router

api_router = APIRouter()
api_router.include_router(audit_router)
api_router.include_router(auth_router)
api_router.include_router(catalog_attributes_router, prefix="/catalog")
api_router.include_router(catalog_brands_router, prefix="/catalog")
api_router.include_router(catalog_categories_router, prefix="/catalog")
api_router.include_router(catalog_channels_router, prefix="/catalog")
api_router.include_router(catalog_collections_router, prefix="/catalog")
api_router.include_router(catalog_coupons_router, prefix="/catalog")
api_router.include_router(catalog_custom_fields_router, prefix="/catalog")
api_router.include_router(catalog_media_router, prefix="/catalog")
api_router.include_router(catalog_pricing_router, prefix="/catalog")
api_router.include_router(catalog_products_router, prefix="/catalog")
api_router.include_router(catalog_product_channels_router, prefix="/catalog")
api_router.include_router(catalog_product_types_router, prefix="/catalog")
api_router.include_router(catalog_seo_router, prefix="/catalog")
api_router.include_router(catalog_tags_router, prefix="/catalog")
api_router.include_router(catalog_taxes_router, prefix="/catalog")
api_router.include_router(catalog_variants_router, prefix="/catalog")
api_router.include_router(dashboard_router)
api_router.include_router(files_router)
api_router.include_router(notifications_router)
api_router.include_router(organizations_router)
api_router.include_router(rbac_router)

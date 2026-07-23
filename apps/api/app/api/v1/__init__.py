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
from app.api.v1.cart.routes import router as cart_router
from app.api.v1.checkout.routes import router as checkout_router
from app.api.v1.customers.auth_routes import router as customers_auth_router
from app.api.v1.customers.portal_routes import router as customers_portal_router
from app.api.v1.customers.routes import router as customers_router
from app.api.v1.dashboard.routes import router as dashboard_router
from app.api.v1.files.routes import router as files_router
from app.api.v1.invoices.routes import router as invoices_router
from app.api.v1.orders.routes import router as orders_router
from app.api.v1.inventory.adjustments.routes import router as inventory_adjustments_router
from app.api.v1.inventory.barcodes.routes import router as inventory_barcodes_router
from app.api.v1.inventory.batches.routes import router as inventory_batches_router
from app.api.v1.inventory.cycle_counts.routes import router as inventory_cycle_counts_router
from app.api.v1.inventory.goods_receipts.routes import router as inventory_goods_receipts_router
from app.api.v1.inventory.purchase_orders.routes import router as inventory_purchase_orders_router
from app.api.v1.inventory.reorder_rules.routes import router as inventory_reorder_rules_router
from app.api.v1.inventory.serial_numbers.routes import router as inventory_serial_numbers_router
from app.api.v1.inventory.stock.routes import router as inventory_stock_router
from app.api.v1.inventory.transfers.routes import router as inventory_transfers_router
from app.api.v1.inventory.warehouses.routes import router as inventory_warehouses_router
from app.api.v1.notifications.routes import router as notifications_router
from app.api.v1.organizations.routes import router as organizations_router
from app.api.v1.rbac.routes import router as rbac_router
from app.api.v1.refunds.routes import router as refunds_router
from app.api.v1.returns.routes import router as returns_router
from app.api.v1.shipping.analytics.routes import router as shipping_analytics_router
from app.api.v1.shipping.pickups.routes import router as shipping_pickups_router
from app.api.v1.shipping.providers.routes import router as shipping_providers_router
from app.api.v1.shipping.rates.routes import router as shipping_rates_router
from app.api.v1.shipping.return_shipments.routes import router as shipping_return_shipments_router
from app.api.v1.shipping.rules.routes import router as shipping_rules_router
from app.api.v1.shipping.shipments.routes import router as shipping_shipments_router
from app.api.v1.shipping.webhooks.routes import router as shipping_webhooks_router
from app.api.v1.wishlist.routes import router as wishlist_router

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
api_router.include_router(cart_router)
api_router.include_router(checkout_router)
api_router.include_router(customers_auth_router)
api_router.include_router(customers_portal_router)
api_router.include_router(customers_router)
api_router.include_router(dashboard_router)
api_router.include_router(files_router)
api_router.include_router(inventory_adjustments_router, prefix="/inventory")
api_router.include_router(inventory_barcodes_router, prefix="/inventory")
api_router.include_router(inventory_batches_router, prefix="/inventory")
api_router.include_router(inventory_cycle_counts_router, prefix="/inventory")
api_router.include_router(inventory_goods_receipts_router, prefix="/inventory")
api_router.include_router(inventory_purchase_orders_router, prefix="/inventory")
api_router.include_router(inventory_reorder_rules_router, prefix="/inventory")
api_router.include_router(inventory_serial_numbers_router, prefix="/inventory")
api_router.include_router(inventory_stock_router, prefix="/inventory")
api_router.include_router(inventory_transfers_router, prefix="/inventory")
api_router.include_router(inventory_warehouses_router, prefix="/inventory")
api_router.include_router(invoices_router)
api_router.include_router(notifications_router)
api_router.include_router(orders_router)
api_router.include_router(organizations_router)
api_router.include_router(rbac_router)
api_router.include_router(refunds_router)
api_router.include_router(returns_router)
api_router.include_router(shipping_analytics_router, prefix="/shipping")
api_router.include_router(shipping_pickups_router, prefix="/shipping")
api_router.include_router(shipping_providers_router, prefix="/shipping")
api_router.include_router(shipping_rates_router, prefix="/shipping")
api_router.include_router(shipping_return_shipments_router, prefix="/shipping")
api_router.include_router(shipping_rules_router, prefix="/shipping")
api_router.include_router(shipping_shipments_router, prefix="/shipping")
api_router.include_router(shipping_webhooks_router, prefix="/shipping")
api_router.include_router(wishlist_router)

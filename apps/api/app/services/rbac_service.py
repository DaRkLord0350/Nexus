from typing import NamedTuple

from app.models.permission import Permission
from app.models.role import Role
from app.models.role_permission import RolePermission
from app.repositories.permission_repository import PermissionRepository
from app.repositories.role_repository import RoleRepository
from app.repositories.user_role_repository import UserRoleRepository


class DefaultRole(NamedTuple):
    description: str
    permissions: list[str]


class RBACService:
    DEFAULT_PERMISSIONS = [
        ("products", "Products", "Manage product catalogs and pricing."),
        ("orders", "Orders", "Manage customer orders and order workflows."),
        ("inventory", "Inventory", "Manage stock levels and inventory locations."),
        ("warehouse", "Warehouse", "Manage warehouse operations and fulfillment."),
        ("finance", "Finance", "Manage billing, invoices, and financial reporting."),
        ("analytics", "Analytics", "View dashboards and analytics reports."),
        ("users", "Users", "Manage organization users and access control."),
        ("settings", "Settings", "Manage organization and system settings."),
        ("files", "Files", "Manage uploaded files and folders."),
        ("audit", "Audit Logs", "View and export organization audit logs."),
        ("ai", "AI", "Manage AI powered automation and assistive workflows."),
        ("shipping", "Shipping", "Manage shipping rules and carrier integrations."),
        ("marketplace", "Marketplace", "Manage marketplace integrations and listings."),
        ("catalog.categories.view", "View Categories", "View product categories."),
        ("catalog.categories.manage", "Manage Categories", "Create, edit, delete, and restore product categories."),
        ("catalog.brands.view", "View Brands", "View product brands."),
        ("catalog.brands.manage", "Manage Brands", "Create, edit, delete, and restore product brands."),
        ("catalog.attributes.view", "View Attributes", "View product attributes and their values."),
        ("catalog.attributes.manage", "Manage Attributes", "Create, edit, and delete product attributes and their values."),
        ("catalog.products.view", "View Products", "View products in the catalog."),
        ("catalog.products.create", "Create Products", "Create new products."),
        ("catalog.products.edit", "Edit Products", "Edit, publish, and archive products."),
        ("catalog.products.delete", "Delete Products", "Delete and restore products."),
        ("catalog.variants.manage", "Manage Variants", "Create, edit, and delete product variants."),
        ("catalog.media.manage", "Manage Media", "Upload, reorder, and delete product and variant media."),
        ("catalog.collections.view", "View Collections", "View manual and dynamic product collections."),
        ("catalog.collections.manage", "Manage Collections", "Create, edit, and delete product collections."),
        ("catalog.pricing.manage", "Manage Pricing", "Create, edit, and delete product and variant pricing."),
        ("catalog.tax.manage", "Manage Tax", "Create, edit, and delete tax classes and tax rates."),
        ("catalog.coupons.view", "View Coupons", "View coupons and validate codes."),
        ("catalog.coupons.manage", "Manage Coupons", "Create, edit, and delete coupons."),
        ("catalog.tags.manage", "Manage Tags", "Create, edit, and delete product tags."),
        ("catalog.product_types.manage", "Manage Product Types", "Create, edit, and delete product types and their attribute sets."),
        ("catalog.channels.manage", "Manage Channels", "Create, edit, and delete sales channels and assign products to them."),
        ("catalog.custom_fields.manage", "Manage Custom Fields", "Create, edit, and delete custom field definitions and their values."),
        ("inventory.warehouses.view", "View Warehouses", "View warehouses, zones, and bin locations."),
        ("inventory.warehouses.manage", "Manage Warehouses", "Create, edit, delete, and restore warehouses, zones, and bin locations."),
        ("inventory.stock.view", "View Stock", "View stock levels and inventory transaction history."),
        ("inventory.stock.manage", "Manage Stock", "Edit stock configuration such as bin, min/max, and reorder point."),
        ("inventory.barcodes.view", "View Barcodes", "View barcodes and QR codes for products, variants, and warehouse entities."),
        ("inventory.barcodes.manage", "Manage Barcodes", "Create, edit, and delete barcodes and QR codes."),
        ("inventory.batches.view", "View Batches", "View batches for FIFO/FEFO tracking, including expiry dates."),
        ("inventory.batches.manage", "Manage Batches", "Create, edit, and delete batches."),
        ("inventory.serials.view", "View Serial Numbers", "View and scan serial numbers."),
        ("inventory.serials.manage", "Manage Serial Numbers", "Create, import, edit, and delete serial numbers."),
        ("inventory.purchase_orders.view", "View Purchase Orders", "View purchase orders and their line items."),
        ("inventory.purchase_orders.create", "Create Purchase Orders", "Create new purchase orders."),
        ("inventory.purchase_orders.edit", "Edit Purchase Orders", "Edit, send, and cancel purchase orders."),
        ("inventory.purchase_orders.delete", "Delete Purchase Orders", "Delete draft purchase orders."),
        ("inventory.goods_receipts.view", "View Goods Receipts", "View goods receipts and their line items."),
        ("inventory.goods_receipts.create", "Create Goods Receipts", "Create draft goods receipts and edit their line items."),
        ("inventory.goods_receipts.manage", "Manage Goods Receipts", "Complete and cancel goods receipts, applying stock movements."),
        ("inventory.transfers.view", "View Stock Transfers", "View stock transfers between warehouses and their line items."),
        ("inventory.transfers.create", "Create Stock Transfers", "Create draft stock transfers and edit their line items."),
        ("inventory.transfers.manage", "Manage Stock Transfers", "Pack, ship, receive, and cancel stock transfers."),
        ("inventory.adjustments.view", "View Stock Adjustments", "View the stock adjustment audit trail."),
        ("inventory.adjustments.create", "Create Stock Adjustments", "Record manual stock adjustments (damage, lost, found, audit)."),
        ("inventory.cycle_counts.view", "View Cycle Counts", "View cycle counts and their line items."),
        ("inventory.cycle_counts.create", "Create Cycle Counts", "Schedule cycle counts and record counted quantities."),
        ("inventory.cycle_counts.manage", "Manage Cycle Counts", "Complete and cancel cycle counts, applying stock variances."),
        ("inventory.reorder_rules.view", "View Reorder Rules", "View reorder rules and low-stock suggestions."),
        ("inventory.reorder_rules.manage", "Manage Reorder Rules", "Create, edit, and delete reorder rules."),
        ("customers.view", "View Customers", "View customer profiles and address books."),
        ("customers.manage", "Manage Customers", "Create, edit, delete, and restore customers and their addresses."),
        ("orders.view", "View Orders", "View orders, their line items, timeline, and notes."),
        ("orders.create", "Create Orders", "Create manual orders and convert carts at checkout."),
        ("orders.edit", "Edit Orders", "Edit order details, add notes, and advance the order workflow."),
        ("orders.fulfill", "Fulfill Orders", "Ship, mark out for delivery, deliver, and adjust fulfillment status."),
        ("orders.cancel", "Cancel Orders", "Cancel orders and trigger inventory restocking."),
        ("returns.view", "View Returns", "View return requests, their items, and inspection status."),
        ("returns.manage", "Manage Returns", "Approve, reject, receive, inspect, and complete return requests."),
        ("refunds.view", "View Refunds", "View refund requests and their approval status."),
        ("refunds.manage", "Manage Refunds", "Approve, reject, and process refunds."),
        ("shipping.providers.view", "View Shipping Providers", "View configured shipping providers and their capabilities."),
        ("shipping.providers.manage", "Manage Shipping Providers", "Create, edit, and delete shipping provider configurations."),
        ("shipping.shipments.view", "View Shipments", "View shipments, their items, and tracking history."),
        ("shipping.shipments.manage", "Manage Shipments", "Create shipments, generate labels, and update shipment status."),
        ("shipping.rates.view", "View Shipping Rates", "View and compare shipping rates across providers."),
        ("shipping.rates.manage", "Manage Shipping Rates", "Create, edit, and delete shipping rate cards."),
        ("shipping.pickups.view", "View Pickups", "View scheduled carrier pickups."),
        ("shipping.pickups.manage", "Manage Pickups", "Schedule, reschedule, and cancel carrier pickups."),
        ("shipping.rules.view", "View Shipping Rules", "View the shipping rules engine configuration."),
        ("shipping.rules.manage", "Manage Shipping Rules", "Create, edit, and delete shipping rules."),
        ("shipping.returns.view", "View Return Shipments", "View reverse-logistics return shipments and tracking."),
        ("shipping.returns.manage", "Manage Return Shipments", "Create and manage reverse-logistics return shipments."),
        ("shipping.analytics.view", "View Shipping Analytics", "View courier performance and shipping analytics dashboards."),
    ]

    DEFAULT_ROLES = {
        "Owner": DefaultRole(
            description="Full access to all organization resources and administration.",
            permissions=[perm[0] for perm in DEFAULT_PERMISSIONS],
        ),
        "Admin": DefaultRole(
            description="Administrative access across organization management and commerce workflows.",
            permissions=[perm[0] for perm in DEFAULT_PERMISSIONS],
        ),
        "Manager": DefaultRole(
            description="Manage products, orders, inventory, and analytics.",
            permissions=[
                "products", "orders", "inventory", "analytics",
                "catalog.categories.view", "catalog.categories.manage",
                "catalog.brands.view", "catalog.brands.manage",
                "catalog.attributes.view", "catalog.attributes.manage",
                "catalog.products.view", "catalog.products.create", "catalog.products.edit", "catalog.products.delete",
                "catalog.variants.manage", "catalog.media.manage",
                "catalog.collections.view", "catalog.collections.manage",
                "catalog.pricing.manage", "catalog.tax.manage",
                "catalog.coupons.view", "catalog.coupons.manage",
                "catalog.tags.manage", "catalog.product_types.manage", "catalog.channels.manage",
                "catalog.custom_fields.manage",
                "inventory.warehouses.view", "inventory.warehouses.manage",
                "inventory.stock.view", "inventory.stock.manage",
                "inventory.barcodes.view", "inventory.barcodes.manage",
                "inventory.batches.view", "inventory.batches.manage",
                "inventory.serials.view", "inventory.serials.manage",
                "inventory.purchase_orders.view", "inventory.purchase_orders.create",
                "inventory.purchase_orders.edit", "inventory.purchase_orders.delete",
                "inventory.goods_receipts.view", "inventory.goods_receipts.create", "inventory.goods_receipts.manage",
                "inventory.transfers.view", "inventory.transfers.create", "inventory.transfers.manage",
                "inventory.adjustments.view", "inventory.adjustments.create",
                "inventory.cycle_counts.view", "inventory.cycle_counts.create", "inventory.cycle_counts.manage",
                "inventory.reorder_rules.view", "inventory.reorder_rules.manage",
                "customers.view", "customers.manage",
                "orders.view", "orders.create", "orders.edit", "orders.fulfill", "orders.cancel",
                "returns.view", "returns.manage", "refunds.view", "refunds.manage",
                "shipping.providers.view", "shipping.providers.manage",
                "shipping.shipments.view", "shipping.shipments.manage",
                "shipping.rates.view", "shipping.rates.manage",
                "shipping.pickups.view", "shipping.pickups.manage",
                "shipping.rules.view", "shipping.rules.manage",
                "shipping.returns.view", "shipping.returns.manage",
                "shipping.analytics.view",
            ],
        ),
        "Warehouse Manager": DefaultRole(
            description="Manage warehouse and inventory operations.",
            permissions=[
                "inventory", "warehouse",
                "inventory.warehouses.view", "inventory.warehouses.manage",
                "inventory.stock.view", "inventory.stock.manage",
                "inventory.barcodes.view", "inventory.barcodes.manage",
                "inventory.batches.view", "inventory.batches.manage",
                "inventory.serials.view", "inventory.serials.manage",
                "inventory.purchase_orders.view", "inventory.purchase_orders.create", "inventory.purchase_orders.edit",
                "inventory.goods_receipts.view", "inventory.goods_receipts.create", "inventory.goods_receipts.manage",
                "inventory.transfers.view", "inventory.transfers.create", "inventory.transfers.manage",
                "inventory.adjustments.view", "inventory.adjustments.create",
                "inventory.cycle_counts.view", "inventory.cycle_counts.create", "inventory.cycle_counts.manage",
                "inventory.reorder_rules.view", "inventory.reorder_rules.manage",
                "orders.view", "orders.fulfill",
                "returns.view", "returns.manage",
                "shipping.providers.view", "shipping.shipments.view", "shipping.shipments.manage",
                "shipping.pickups.view", "shipping.pickups.manage", "shipping.rates.view",
                "shipping.returns.view", "shipping.returns.manage",
            ],
        ),
        "Finance": DefaultRole(
            description="Manage financial reporting and billing workflows.",
            permissions=["finance", "orders", "catalog.pricing.manage", "catalog.tax.manage", "customers.view", "orders.view", "refunds.view", "refunds.manage", "shipping.analytics.view"],
        ),
        "Marketing": DefaultRole(
            description="Manage campaigns, marketplace, and analytics.",
            permissions=[
                "analytics", "ai", "marketplace",
                "catalog.collections.view", "catalog.collections.manage",
                "catalog.coupons.view", "catalog.coupons.manage",
            ],
        ),
        "Support": DefaultRole(
            description="Provide customer support and order assistance.",
            permissions=["orders", "users", "customers.view", "customers.manage", "orders.view", "orders.edit", "orders.cancel", "returns.view", "returns.manage", "refunds.view", "shipping.shipments.view"],
        ),
        "Staff": DefaultRole(
            description="Day-to-day operational access based on assigned tasks.",
            permissions=["orders", "products", "catalog.categories.view", "catalog.brands.view", "catalog.attributes.view", "catalog.products.view", "catalog.collections.view", "catalog.coupons.view", "customers.view", "orders.view"],
        ),
        "Custom Role": DefaultRole(
            description="Custom role with organization-specific permissions.",
            permissions=[],
        ),
    }

    def __init__(self, session, organization_id: str | None = None, is_superuser: bool = False):
        self.session = session
        self.organization_id = organization_id
        self.is_superuser = is_superuser
        self.role_repo = RoleRepository(session, organization_id, is_superuser)
        self.permission_repo = PermissionRepository(session, organization_id, is_superuser)
        self.user_role_repo = UserRoleRepository(session, organization_id, is_superuser)

    async def initialize_default_roles_and_permissions(self) -> None:
        permission_map: dict[str, Permission] = {p.code: p for p in await self.permission_repo.list()}
        missing_permissions = [
            Permission(code=code, name=name, description=description)
            for code, name, description in self.DEFAULT_PERMISSIONS
            if code not in permission_map
        ]
        if missing_permissions:
            for permission in await self.permission_repo.bulk_create(missing_permissions):
                permission_map[permission.code] = permission

        existing_roles = {role.name: role for role in await self.role_repo.list_plain()}
        missing_roles = [
            Role(name=role_name, description=default_role.description, built_in=True)
            for role_name, default_role in self.DEFAULT_ROLES.items()
            if role_name not in existing_roles
        ]
        if missing_roles:
            for role in await self.role_repo.bulk_create(missing_roles):
                existing_roles[role.name] = role

        role_ids = [role.id for role in existing_roles.values()]
        permission_ids_by_role = await self.role_repo.get_permission_ids_for_roles(role_ids)

        new_links: list[RolePermission] = []
        for role_name, default_role in self.DEFAULT_ROLES.items():
            role = existing_roles[role_name]
            existing_permission_ids = permission_ids_by_role.get(role.id, set())
            for permission_code in default_role.permissions:
                permission = permission_map.get(permission_code)
                if permission and permission.id not in existing_permission_ids:
                    new_links.append(RolePermission(role_id=role.id, permission_id=permission.id, organization_id=role.organization_id))

        if new_links:
            await self.role_repo.bulk_add_permissions(new_links)

    async def create_role(self, name: str, description: str | None = None, permission_codes: list[str] | None = None, built_in: bool = False) -> Role:
        existing_role = await self.role_repo.get_by_name(name)
        if existing_role:
            return existing_role

        role = Role(name=name, description=description, built_in=built_in)
        role = await self.role_repo.create(role)
        if permission_codes:
            for permission_code in permission_codes:
                permission = await self.permission_repo.get_by_code(permission_code)
                if permission:
                    await self.role_repo.add_permission(role, permission)
        return role

    async def assign_role_to_user(self, user_id: str, role_id: str) -> None:
        role = await self.role_repo.get_by_id(role_id)
        if not role:
            raise ValueError("Role not found.")
        await self.user_role_repo.assign(user_id=user_id, role=role)

    async def remove_role_from_user(self, user_id: str, role_id: str) -> None:
        await self.user_role_repo.unassign(user_id=user_id, role_id=role_id)

    async def list_roles(self) -> list[Role]:
        return await self.role_repo.list()

    async def list_permissions(self) -> list[Permission]:
        return await self.permission_repo.list()

    async def get_user_roles(self, user_id: str) -> list[Role]:
        user_roles = await self.user_role_repo.list_for_user(user_id)
        return [user_role.role for user_role in user_roles if user_role.role]

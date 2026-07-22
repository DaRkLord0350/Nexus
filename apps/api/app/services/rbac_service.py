from typing import NamedTuple

from app.models.permission import Permission
from app.models.role import Role
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
            ],
        ),
        "Warehouse Manager": DefaultRole(
            description="Manage warehouse and inventory operations.",
            permissions=["inventory", "warehouse"],
        ),
        "Finance": DefaultRole(
            description="Manage financial reporting and billing workflows.",
            permissions=["finance", "orders", "catalog.pricing.manage", "catalog.tax.manage"],
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
            permissions=["orders", "users"],
        ),
        "Staff": DefaultRole(
            description="Day-to-day operational access based on assigned tasks.",
            permissions=["orders", "products", "catalog.categories.view", "catalog.brands.view", "catalog.attributes.view", "catalog.products.view", "catalog.collections.view", "catalog.coupons.view"],
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
        permission_map: dict[str, Permission] = {}
        for code, name, description in self.DEFAULT_PERMISSIONS:
            permission = await self.permission_repo.get_by_code(code)
            if not permission:
                permission = await self.permission_repo.create(
                    Permission(code=code, name=name, description=description)
                )
            permission_map[code] = permission

        for role_name, default_role in self.DEFAULT_ROLES.items():
            role = await self.role_repo.get_by_name(role_name)
            if not role:
                role = await self.role_repo.create(
                    Role(name=role_name, description=default_role.description, built_in=True)
                )

            existing_permission_ids = await self.role_repo.get_permission_ids(role.id)
            for permission_code in default_role.permissions:
                permission = permission_map.get(permission_code)
                if permission and permission.id not in existing_permission_ids:
                    await self.role_repo.add_permission(role, permission)

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

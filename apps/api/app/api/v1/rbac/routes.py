from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit_context import AuditContext
from app.dependencies import get_audit_context, get_current_active_user, get_db, require_permission
from app.schemas.role import RoleCreateRequest, RoleRead
from app.schemas.permission import PermissionRead
from app.services.audit_service import AuditService
from app.services.permission_service import PermissionService
from app.services.rbac_service import RBACService

router = APIRouter(prefix="/rbac", tags=["rbac"])


@router.get("/permissions", response_model=list[PermissionRead])
async def list_permissions(current_user=Depends(get_current_active_user), db: AsyncSession = Depends(get_db)):
    permission_service = PermissionService(db, current_user.organization_id, current_user.is_superuser)
    permission_codes = await permission_service.get_user_permissions(current_user.id)
    return [PermissionRead(code=code) for code in permission_codes]


@router.get("/roles", response_model=list[RoleRead])
async def list_roles(current_user=Depends(get_current_active_user), db: AsyncSession = Depends(get_db)):
    rbac_service = RBACService(db, current_user.organization_id, current_user.is_superuser)
    roles = await rbac_service.list_roles()
    return [RoleRead(
        id=role.id,
        name=role.name,
        description=role.description,
        built_in=role.built_in,
        organization_id=role.organization_id,
        permissions=[permission.permission.code for permission in role.permissions],
        created_at=role.created_at,
        updated_at=role.updated_at,
    ) for role in roles]


@router.post("/roles", response_model=RoleRead, status_code=status.HTTP_201_CREATED)
async def create_role(
    data: RoleCreateRequest,
    current_user=Depends(require_permission("settings")),
    db: AsyncSession = Depends(get_db),
    audit_context: AuditContext = Depends(get_audit_context),
):
    rbac_service = RBACService(db, current_user.organization_id, current_user.is_superuser)
    role = await rbac_service.create_role(data.name, data.description, data.permission_codes, built_in=False)
    role = await rbac_service.role_repo.get_by_id(role.id)
    await AuditService(db, current_user.organization_id).log(
        action="create",
        module="rbac",
        entity="Role",
        entity_id=role.id,
        user_id=current_user.id,
        after={"name": role.name, "permissions": data.permission_codes},
        context=audit_context,
    )
    return RoleRead(
        id=role.id,
        name=role.name,
        description=role.description,
        built_in=role.built_in,
        organization_id=role.organization_id,
        permissions=[permission.permission.code for permission in role.permissions],
        created_at=role.created_at,
        updated_at=role.updated_at,
    )


@router.post("/roles/{role_id}/assign")
async def assign_role_to_user(
    role_id: str,
    data: dict[str, str],
    current_user=Depends(require_permission("users")),
    db: AsyncSession = Depends(get_db),
    audit_context: AuditContext = Depends(get_audit_context),
):
    user_id = data.get("user_id")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="user_id is required.")
    rbac_service = RBACService(db, current_user.organization_id, current_user.is_superuser)
    await rbac_service.assign_role_to_user(user_id, role_id)
    await AuditService(db, current_user.organization_id).log(
        action="role_assignment",
        module="rbac",
        entity="UserRole",
        entity_id=role_id,
        user_id=current_user.id,
        after={"target_user_id": user_id, "role_id": role_id},
        context=audit_context,
    )
    return {"detail": "Role assigned successfully."}


@router.delete("/roles/{role_id}/assignments")
async def remove_role_from_user(
    role_id: str,
    data: dict[str, str],
    current_user=Depends(require_permission("users")),
    db: AsyncSession = Depends(get_db),
    audit_context: AuditContext = Depends(get_audit_context),
):
    user_id = data.get("user_id")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="user_id is required.")
    rbac_service = RBACService(db, current_user.organization_id, current_user.is_superuser)
    await rbac_service.remove_role_from_user(user_id, role_id)
    await AuditService(db, current_user.organization_id).log(
        action="role_removal",
        module="rbac",
        entity="UserRole",
        entity_id=role_id,
        user_id=current_user.id,
        before={"target_user_id": user_id, "role_id": role_id},
        context=audit_context,
    )
    return {"detail": "Role removed successfully."}

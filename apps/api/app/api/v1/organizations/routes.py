from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit_context import AuditContext
from app.dependencies import get_audit_context, get_current_active_user, get_db, require_permission
from app.schemas.invitation import AcceptInvitationRequest, InviteMemberRequest
from app.schemas.organization import OrganizationRead, OrganizationUpdateRequest
from app.schemas.user import UserRead
from app.services.audit_service import AuditService
from app.services.organization_service import OrganizationService

router = APIRouter(prefix="/organizations", tags=["organizations"])


@router.get("/me", response_model=OrganizationRead)
async def read_organization(current_user=Depends(get_current_active_user), db: AsyncSession = Depends(get_db)):
    organization = await OrganizationService(db).get_organization(current_user.organization_id)
    if not organization:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found.")
    return organization


@router.patch("/{organization_id}", response_model=OrganizationRead)
async def update_organization(
    organization_id: str,
    data: OrganizationUpdateRequest,
    current_user=Depends(require_permission("settings")),
    db: AsyncSession = Depends(get_db),
    audit_context: AuditContext = Depends(get_audit_context),
):
    if not (current_user.is_superuser or current_user.organization_id == organization_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden.")
    changes = data.model_dump(exclude_unset=True)
    organization = await OrganizationService(db).update_organization(organization_id, changes)
    await AuditService(db, organization_id).log(
        action="settings_change",
        module="organizations",
        entity="Organization",
        entity_id=organization_id,
        user_id=current_user.id,
        after=changes,
        context=audit_context,
    )
    return organization


@router.get("/{organization_id}/members", response_model=list[UserRead])
async def list_members(organization_id: str, current_user=Depends(require_permission("users")), db: AsyncSession = Depends(get_db)):
    if not (current_user.is_superuser or current_user.organization_id == organization_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden.")
    return await OrganizationService(db).list_members(organization_id)


@router.post("/{organization_id}/invite")
async def invite_member(
    organization_id: str,
    invite: InviteMemberRequest,
    current_user=Depends(require_permission("users")),
    db: AsyncSession = Depends(get_db),
    audit_context: AuditContext = Depends(get_audit_context),
):
    if not (current_user.is_superuser or current_user.organization_id == organization_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden.")
    invitation = await OrganizationService(db).invite_member(organization_id, current_user.id, invite.email)
    await AuditService(db, organization_id).log(
        action="invitation",
        module="organizations",
        entity="OrganizationInvitation",
        entity_id=invitation.id,
        user_id=current_user.id,
        after={"email": invite.email},
        context=audit_context,
    )
    return {"detail": "Invitation sent.", "invitation_id": invitation.id}


@router.post("/invitations/accept", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def accept_invitation(data: AcceptInvitationRequest, db: AsyncSession = Depends(get_db), audit_context: AuditContext = Depends(get_audit_context)):
    user = await OrganizationService(db).accept_invitation(data.token, data.first_name, data.last_name, data.password)
    await AuditService(db, user.organization_id).log(
        action="create",
        module="organizations",
        entity="User",
        entity_id=user.id,
        user_id=user.id,
        after={"email": user.email},
        context=audit_context,
    )
    return user


@router.post("/{organization_id}/transfer-ownership")
async def transfer_ownership(
    organization_id: str,
    data: dict[str, str],
    current_user=Depends(require_permission("settings")),
    db: AsyncSession = Depends(get_db),
    audit_context: AuditContext = Depends(get_audit_context),
):
    if not (current_user.is_superuser or current_user.organization_id == organization_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden.")
    new_owner_id = data.get("new_owner_id")
    if not new_owner_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="new_owner_id is required.")
    await OrganizationService(db).transfer_ownership(organization_id, current_user.id, new_owner_id)
    await AuditService(db, organization_id).log(
        action="role_assignment",
        module="organizations",
        entity="Organization",
        entity_id=organization_id,
        user_id=current_user.id,
        before={"owner_id": current_user.id},
        after={"owner_id": new_owner_id},
        context=audit_context,
    )
    return {"detail": "Ownership transferred successfully."}


@router.post("/{organization_id}/deactivate", response_model=OrganizationRead)
async def deactivate_organization(
    organization_id: str,
    current_user=Depends(require_permission("settings")),
    db: AsyncSession = Depends(get_db),
    audit_context: AuditContext = Depends(get_audit_context),
):
    if not (current_user.is_superuser or current_user.organization_id == organization_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden.")
    organization = await OrganizationService(db).deactivate_organization(organization_id)
    await AuditService(db, organization_id).log(
        action="settings_change",
        module="organizations",
        entity="Organization",
        entity_id=organization_id,
        user_id=current_user.id,
        after={"status": "suspended"},
        context=audit_context,
    )
    return organization


@router.post("/{organization_id}/delete", response_model=OrganizationRead)
async def delete_organization(
    organization_id: str,
    current_user=Depends(require_permission("settings")),
    db: AsyncSession = Depends(get_db),
    audit_context: AuditContext = Depends(get_audit_context),
):
    if not (current_user.is_superuser or current_user.organization_id == organization_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden.")
    organization = await OrganizationService(db).delete_organization(organization_id)
    await AuditService(db, organization_id).log(
        action="delete",
        module="organizations",
        entity="Organization",
        entity_id=organization_id,
        user_id=current_user.id,
        context=audit_context,
    )
    return organization

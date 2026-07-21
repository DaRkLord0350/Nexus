from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.organization import Organization
from app.repositories.organization_repository import OrganizationRepository
from app.repositories.organization_invitation_repository import OrganizationInvitationRepository
from app.repositories.session_repository import SessionRepository
from app.repositories.user_repository import UserRepository


class DashboardService:
    def __init__(self, session: AsyncSession, organization_id: str | None = None, is_superuser: bool = False):
        self.session = session
        self.organization_id = organization_id
        self.is_superuser = is_superuser
        self.organization_repo = OrganizationRepository(session)
        self.user_repo = UserRepository(session, organization_id, is_superuser)
        self.session_repo = SessionRepository(session, organization_id, is_superuser)
        self.invitation_repo = OrganizationInvitationRepository(session, organization_id, is_superuser)

    async def get_dashboard(self) -> dict:
        organization = None
        if self.organization_id:
            organization = await self.organization_repo.get_by_id(self.organization_id)

        total_users = await self.user_repo.count()
        verified_users = await self.user_repo.count_verified()
        active_sessions = await self.session_repo.count_recent(7)
        pending_invites = await self.invitation_repo.count_pending()
        recent_sessions = await self.session_repo.list_recent(10)

        last_week_date = datetime.utcnow() - timedelta(days=7)
        return {
            "organization": {
                "id": organization.id,
                "name": organization.name,
                "slug": organization.slug,
                "status": organization.status.value,
            } if organization else None,
            "metrics": [
                {
                    "id": "customers",
                    "title": "Customers",
                    "value": total_users,
                    "subtitle": "Total organization users",
                },
                {
                    "id": "verified_users",
                    "title": "Verified Users",
                    "value": verified_users,
                    "subtitle": "Users with verified email",
                },
                {
                    "id": "active_sessions",
                    "title": "Active Sessions",
                    "value": active_sessions,
                    "subtitle": "Sessions in the last 7 days",
                },
                {
                    "id": "pending_invitations",
                    "title": "Pending Invitations",
                    "value": pending_invites,
                    "subtitle": "Outstanding organization invitations",
                },
            ],
            "recent_activity": [
                {
                    "id": session.id,
                    "user_id": session.user_id,
                    "user_name": f"{session.user.first_name} {session.user.last_name}" if session.user else "Unknown",
                    "device_name": session.device_name,
                    "ip_address": session.ip_address,
                    "last_active_at": session.last_active_at,
                    "status": "active" if not session.revoked else "revoked",
                }
                for session in recent_sessions
            ],
            "summary": {
                "week_start": last_week_date,
                "generated_at": datetime.utcnow(),
            },
        }

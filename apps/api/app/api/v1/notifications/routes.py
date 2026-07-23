from fastapi import APIRouter, Depends, HTTPException, Query, status, WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.websockets import WebSocketState
import asyncio

from app.core.audit_context import AuditContext
from app.db import AsyncSessionLocal
from app.dependencies import get_audit_context, get_current_active_user, get_db, require_permission
from app.models.user import User
from app.repositories.session_repository import SessionRepository
from app.repositories.user_repository import UserRepository
from app.schemas.notification import (
    NotificationChannel,
    NotificationCreateRequest,
    NotificationItem,
    NotificationListResponse,
    NotificationPreferenceItem,
    NotificationPreferenceUpdateRequest,
    UnreadCountResponse,
)
from app.services.audit_service import AuditService
from app.services.notification_service import NotificationService
from app.utils.security import decode_token
from app.core.redis import redis_client

router = APIRouter(prefix="/notifications", tags=["notifications"])


async def _authenticate_websocket(websocket: WebSocket, db: AsyncSession) -> User:
    authorization = websocket.headers.get("authorization")
    token = None
    if authorization and authorization.lower().startswith("bearer "):
        token = authorization.split(" ", 1)[1].strip()
    else:
        token = websocket.query_params.get("token")

    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication token required.")

    try:
        payload = decode_token(token)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authentication credentials.")

    user_id = payload.get("sub")
    session_id = payload.get("sid")
    organization_id = payload.get("oid")
    if not user_id or not session_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authentication credentials.")

    user = await UserRepository(db, organization_id=organization_id).get_by_id(user_id)
    if not user or not user.is_active or (organization_id and user.organization_id != organization_id):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authentication credentials.")

    session_record = await SessionRepository(db, organization_id=organization_id).get_by_id(session_id)
    if not session_record or session_record.revoked or session_record.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authentication credentials.")

    return user


@router.websocket("/ws")
async def notifications_websocket(websocket: WebSocket):
    await websocket.accept()
    try:
        async with AsyncSessionLocal() as db:
            user = await _authenticate_websocket(websocket, db)
    except HTTPException:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    organization_id = user.organization_id or ""
    user_channel = f"notifications:{organization_id}:{user.id}"
    broadcast_channel = f"notifications:{organization_id}:broadcast"
    pubsub = redis_client.pubsub()
    await pubsub.subscribe(user_channel, broadcast_channel)

    try:
        while websocket.client_state != WebSocketState.DISCONNECTED:
            message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
            if message and message.get("type") == "message":
                payload = message.get("data")
                if isinstance(payload, bytes):
                    payload = payload.decode("utf-8")
                await websocket.send_text(payload)
            await asyncio.sleep(0.1)
    except WebSocketDisconnect:
        pass
    finally:
        await pubsub.unsubscribe(user_channel, broadcast_channel)
        await pubsub.close()


@router.get("/", response_model=NotificationListResponse)
async def list_notifications(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    current_user=Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    notification_service = NotificationService(db, current_user.organization_id, current_user.is_superuser)
    notifications = await notification_service.list_notifications(current_user.id, limit=limit, offset=offset)
    return {"notifications": notifications}


@router.get("/unread-count", response_model=UnreadCountResponse)
async def unread_count(current_user=Depends(get_current_active_user), db: AsyncSession = Depends(get_db)):
    notification_service = NotificationService(db, current_user.organization_id, current_user.is_superuser)
    return {"unread_count": await notification_service.get_unread_count(current_user.id)}


@router.post("/{notification_id}/read")
async def mark_notification_read(notification_id: str, current_user=Depends(get_current_active_user), db: AsyncSession = Depends(get_db)):
    notification_service = NotificationService(db, current_user.organization_id, current_user.is_superuser)
    await notification_service.mark_read(notification_id, current_user.id)
    return {"detail": "Notification marked as read."}


@router.post("/read-all")
async def mark_all_read(current_user=Depends(get_current_active_user), db: AsyncSession = Depends(get_db)):
    notification_service = NotificationService(db, current_user.organization_id, current_user.is_superuser)
    await notification_service.mark_all_read(current_user.id)
    return {"detail": "All notifications marked as read."}


@router.get("/preferences", response_model=list[NotificationPreferenceItem])
async def get_preferences(current_user=Depends(get_current_active_user), db: AsyncSession = Depends(get_db)):
    notification_service = NotificationService(db, current_user.organization_id, current_user.is_superuser)
    preferences = await notification_service.get_preferences(current_user.id)
    return [NotificationPreferenceItem(channel=p.channel, enabled=p.enabled) for p in preferences]


@router.patch("/preferences", response_model=NotificationPreferenceItem)
async def update_preferences(
    data: NotificationPreferenceUpdateRequest,
    current_user=Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    audit_context: AuditContext = Depends(get_audit_context),
):
    notification_service = NotificationService(db, current_user.organization_id, current_user.is_superuser)
    preference = await notification_service.update_preference(current_user.id, NotificationChannel(data.channel), data.enabled)
    await AuditService(db, current_user.organization_id).log(
        action="settings_change",
        module="notifications",
        entity="NotificationPreference",
        entity_id=current_user.id,
        user_id=current_user.id,
        after={"channel": data.channel, "enabled": data.enabled},
        context=audit_context,
    )
    return NotificationPreferenceItem(channel=preference.channel, enabled=preference.enabled)


@router.post("/send")
async def send_notification(data: NotificationCreateRequest, current_user=Depends(require_permission("settings")), db: AsyncSession = Depends(get_db)):
    notification_service = NotificationService(db, current_user.organization_id, current_user.is_superuser)
    await notification_service.send_notification(
        user_id=current_user.id,
        title=data.title,
        message=data.message,
        notification_type=data.type,
        channels=[NotificationChannel(channel) for channel in data.channels],
        actor_id=data.actor_id,
        metadata=data.metadata,
    )
    return {"detail": "Notification dispatched."}

import json

from app.core.redis import redis_client


class NotificationPublisher:
    @staticmethod
    async def publish(organization_id: str, user_id: str, payload: dict) -> None:
        channel = f"notifications:{organization_id}:{user_id}"
        await redis_client.publish(channel, json.dumps(payload))

    @staticmethod
    async def publish_broadcast(organization_id: str, payload: dict) -> None:
        channel = f"notifications:{organization_id}:broadcast"
        await redis_client.publish(channel, json.dumps(payload))

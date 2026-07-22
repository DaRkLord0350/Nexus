pytest_plugins = ["pytest_asyncio"]

import os
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

os.environ["ENVIRONMENT"] = "development"
os.environ["DEBUG"] = "True"
os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:///{ROOT_DIR / 'test.db'}"
os.environ["SECRET_KEY"] = "test-secret"
# Without this, tests pick up the real EMAIL_PROVIDER=ses (and real AWS
# credentials) from apps/api/.env and attempt to send actual emails via SES,
# failing every test that registers a user.
os.environ["EMAIL_PROVIDER"] = "smtp"
os.environ["SMTP_HOST"] = ""
# Same reasoning: apps/api/.env points STORAGE_PROVIDER at real S3, which
# makes file-service tests attempt real AWS calls instead of using the local
# disk adapter each test's tmp_path fixture expects.
os.environ["STORAGE_PROVIDER"] = "local"

# apps/api/.env also points REDIS_URL at a real Upstash instance. Any test that
# triggers a notification (rate limiting is bypassed in tests, but
# NotificationService always publishes) would otherwise make a real network
# call and could flakily fail at interpreter/event-loop shutdown. Swap in an
# in-memory fake before any app module grabs a reference to redis_client.
import fakeredis.aioredis
from app.core import redis as redis_module

redis_module.redis_client = fakeredis.aioredis.FakeRedis(decode_responses=True)

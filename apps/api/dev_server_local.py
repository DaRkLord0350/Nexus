"""Local-only dev server entrypoint used for manual browser verification.

Deliberately overrides DATABASE_URL/STORAGE_PROVIDER/EMAIL_PROVIDER so this
never touches the real RDS/S3/SES resources configured in .env — those are
production credentials and must never be exercised by ad-hoc local runs.
"""
import os
import sys
from pathlib import Path

API_DIR = Path(__file__).resolve().parent

os.environ["ENVIRONMENT"] = "development"
os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:///{API_DIR / 'dev_local.db'}"
os.environ["SECRET_KEY"] = "dev-local-secret-not-for-production"
os.environ["EMAIL_PROVIDER"] = "smtp"
os.environ["SMTP_HOST"] = ""
os.environ["STORAGE_PROVIDER"] = "local"
os.environ["REDIS_URL"] = "redis://localhost:6379/0"

sys.path.insert(0, str(Path(__file__).resolve().parent))

# Swap in an in-memory fake Redis so the rate limiter / notification pub-sub
# don't require (or touch) a real Redis instance for this local-only run.
import fakeredis.aioredis
from app.core import redis as redis_module

redis_module.redis_client = fakeredis.aioredis.FakeRedis(decode_responses=True)

import uvicorn

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=False)

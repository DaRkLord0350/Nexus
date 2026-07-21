import asyncio

import os
import sys

from logging.config import fileConfig

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from sqlalchemy import pool
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine


from alembic import context


# from app.core.config import settings
# from app.db import Base
# import app.models  # ensure models are imported so metadata is populated
try:
    from app.core.config import settings
    print("✓ config imported")
except Exception as e:
    print("config import failed:", repr(e))
    raise

try:
    from app.db import Base
    print("✓ db imported")
except Exception as e:
    print("db import failed:", repr(e))
    raise

try:
    import app.models
    print("✓ models imported")
except Exception as e:
    print("models import failed:", repr(e))
    raise

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

config.set_main_option("sqlalchemy.url", settings.database_url)

target_metadata = Base.metadata


def run_migrations_online() -> None:
    connectable = create_async_engine(settings.database_url, poolclass=pool.NullPool)

    def do_run_migrations(sync_connection):
        context.configure(connection=sync_connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()

    async def async_main() -> None:
        async with connectable.connect() as connection:
            await connection.run_sync(do_run_migrations)

    asyncio.run(async_main())


if context.is_offline_mode():
    raise RuntimeError("Offline migrations are not supported. Use async mode.")
else:
    run_migrations_online()

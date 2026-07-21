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

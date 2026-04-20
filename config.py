import os
import sys
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:
    def load_dotenv(*_args, **_kwargs):
        return False


def _get_int(name: str, default: int) -> int:
    raw_value = os.getenv(name)
    if raw_value in (None, ""):
        return default

    try:
        return int(raw_value)
    except ValueError:
        return default


IS_FROZEN = getattr(sys, "frozen", False)
APP_DIR = Path(sys.executable).resolve().parent if IS_FROZEN else Path(__file__).resolve().parent
RESOURCE_DIR = Path(getattr(sys, "_MEIPASS", APP_DIR)) if IS_FROZEN else APP_DIR

load_dotenv(APP_DIR / ".env")

DATA_DIR = Path(os.getenv("TCS_DATA_DIR", str(APP_DIR / "data"))).expanduser().resolve()
CONTENT_DIR = DATA_DIR / "content"
DB_PATH = DATA_DIR / "tcs.db"
STATIC_DIR = RESOURCE_DIR / "static"

DATA_DIR.mkdir(parents=True, exist_ok=True)
CONTENT_DIR.mkdir(parents=True, exist_ok=True)

DATABASE_URL = f"sqlite:///{DB_PATH.as_posix()}"

MAX_UPLOAD_SIZE = max(_get_int("TCS_MAX_UPLOAD_SIZE", 500 * 1024 * 1024), 1)
ANON_UPLOAD_LIMIT = max(_get_int("TCS_ANON_UPLOAD_LIMIT", 50 * 1024 * 1024), 0)
COMPRESSION_LEVEL = min(max(_get_int("TCS_COMPRESSION_LEVEL", 10), 1), 22)

ADMIN_USERNAME = os.getenv("TCS_ADMIN_USER", "admin")
ADMIN_PASSWORD = os.getenv("TCS_ADMIN_PASS", "tcs2024secure")

JWT_SECRET = os.getenv("TCS_JWT_SECRET", "change-this-dev-jwt-secret-before-production-12345")
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = max(_get_int("TCS_JWT_EXPIRATION_HOURS", 24), 1)

SERVER_HOST = os.getenv("SERVER_HOST", "127.0.0.1")
SERVER_PORT = _get_int("SERVER_PORT", 8000)

SEARCH_INDEX_UPDATE_INTERVAL = 300

from pathlib import Path


# Local environment settings handled by common.py BASE_DIR

DEBUG = True
ALLOWED_HOSTS = ["*"]

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
DB_DIR = BASE_DIR / "database"
DB_DIR.mkdir(parents=True, exist_ok=True)

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": str(DB_DIR / "db.sqlite3"),
    }
}

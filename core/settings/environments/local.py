from pathlib import Path


# Local environment settings handled by common.py BASE_DIR

DEBUG = True
ALLOWED_HOSTS = ["*"]


DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": "/Users/sunday/Documents/Project/swiftAid/app/backend/core/db.sqlite3",
    }
}

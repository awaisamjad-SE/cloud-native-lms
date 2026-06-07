from .base import *

# Local dev settings
DEBUG = True

# Media settings for local development (filesystem fallback)
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent

MEDIA_ROOT = os.environ.get("MEDIA_ROOT", BASE_DIR / "media")
MEDIA_URL = os.environ.get("MEDIA_URL", "/media/")

# Allow using S3 for local testing by setting DEFAULT_FILE_STORAGE env var
# Example: DEFAULT_FILE_STORAGE=storages.backends.s3boto3.S3Boto3Storage
AWS_STORAGE_BUCKET_NAME = os.environ.get("AWS_STORAGE_BUCKET_NAME")
AWS_ACCESS_KEY_ID = os.environ.get("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.environ.get("AWS_SECRET_ACCESS_KEY")

if AWS_STORAGE_BUCKET_NAME and AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY:
	# Ensure django-storages is available in INSTALLED_APPS for convenience
	INSTALLED_APPS += ["storages"]
	STORAGES["default"] = {
		"BACKEND": "apps.accounts.storage.PublicMediaStorage",
	}
	STORAGES["public"] = {
		"BACKEND": "apps.accounts.storage.PublicMediaStorage",
	}
	STORAGES["private"] = {
		"BACKEND": "apps.accounts.storage.PrivateMediaStorage",
	}

# CORS for local frontend development.
CORS_ALLOWED_ORIGINS = [
	"http://localhost:8080",
]
CORS_ALLOW_CREDENTIALS = True

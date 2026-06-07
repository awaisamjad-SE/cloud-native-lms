from .base import *

# Production settings overrides
DEBUG = False

# Configure ALLOWED_HOSTS appropriately for production
ALLOWED_HOSTS = []

# Optional: Use django-storages with S3 for file storage. Ensure you install
# `django-storages[boto3]` and set AWS credentials in the environment or a
# secure secrets store. These values read from environment variables so no
# secret is committed to source control.
import os

INSTALLED_APPS += [
	"storages",
]

# Use S3Boto3 storage backend as the default file storage in production.
# For private buckets and presigned URLs keep `AWS_QUERYSTRING_AUTH = True`.
DEFAULT_FILE_STORAGE = os.environ.get(
	"DEFAULT_FILE_STORAGE", "storages.backends.s3boto3.S3Boto3Storage"
)
STORAGES["default"] = {
	"BACKEND": "apps.accounts.storage.PublicMediaStorage",
}
STORAGES["public"] = {
	"BACKEND": "apps.accounts.storage.PublicMediaStorage",
}
STORAGES["private"] = {
	"BACKEND": "apps.accounts.storage.PrivateMediaStorage",
}

AWS_ACCESS_KEY_ID = os.environ.get("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.environ.get("AWS_SECRET_ACCESS_KEY")
AWS_STORAGE_BUCKET_NAME = os.environ.get("AWS_STORAGE_BUCKET_NAME")
AWS_S3_REGION_NAME = os.environ.get("AWS_S3_REGION_NAME", "us-east-1")
AWS_S3_SIGNATURE_VERSION = os.environ.get("AWS_S3_SIGNATURE_VERSION", "s3v4")
# Keep ACL unset (recommended)
AWS_DEFAULT_ACL = None
# If you want signed URLs for private objects, keep this True (default). Set
# to False for public buckets where direct object URLs are desired.
AWS_QUERYSTRING_AUTH = os.environ.get("AWS_QUERYSTRING_AUTH", "True") in ["True", "true", True]

# Optional: custom domain for public buckets
AWS_S3_CUSTOM_DOMAIN = os.environ.get("AWS_S3_CUSTOM_DOMAIN")


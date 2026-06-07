from storages.backends.s3boto3 import S3Boto3Storage


class PublicMediaStorage(S3Boto3Storage):
	location = "public"
	# Do NOT set an ACL when the target bucket enforces "Bucket owner
	# enforced" (object ownership) — that configuration rejects ACLs.
	# Leave as None so django-storages does not include an ACL on PutObject.
	default_acl = None
	querystring_auth = False


class PrivateMediaStorage(S3Boto3Storage):
	location = "private"
	default_acl = None
	querystring_auth = True
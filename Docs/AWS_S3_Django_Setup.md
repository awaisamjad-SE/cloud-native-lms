# AWS S3 Setup for Django

This guide shows how to use AWS S3 in a Django project for file uploads, including both public and private bucket setups.

## 1) Install the required libraries

Install these packages in your Django environment:

```bash
pip install boto3 django-storages
```

If you manage dependencies with `requirements/base.txt`, add:

```txt
django-storages
boto3
```

## 2) Create the S3 bucket in AWS

1. Open the AWS Console.
2. Go to S3.
3. Click Create bucket.
4. Choose a unique bucket name.
5. Choose your AWS Region and keep it consistent with your Django app.
6. Decide whether the bucket should be public or private:
   - Private bucket: recommended for user uploads.
   - Public bucket: only if files must be accessible by direct URL.

## 3) Bucket public vs private

### Private bucket

Use this when files should not be accessible directly from the browser.

Recommended AWS settings:

- Keep Block Public Access enabled.
- Do not use ACLs if the bucket uses Object Ownership = Bucket owner enforced.
- Use presigned URLs when you need temporary access.

### Public bucket or public prefix

Use this only when files should open directly in the browser.

Recommended AWS settings:

- Disable Block Public Access only if you really need public reads.
- Add a bucket policy that allows `s3:GetObject` for the public prefix.
- Do not rely on ACLs if your bucket rejects ACLs.

Example bucket policy for public files under `public/`:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "PublicReadForPublicPrefix",
      "Effect": "Allow",
      "Principal": "*",
      "Action": "s3:GetObject",
      "Resource": "arn:aws:s3:::YOUR_BUCKET_NAME/public/*"
    }
  ]
}
```

## 4) Create IAM access

Create an IAM user or role with access to the bucket.

Minimum permissions for upload and read:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:PutObject",
        "s3:GetObject",
        "s3:DeleteObject",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::YOUR_BUCKET_NAME",
        "arn:aws:s3:::YOUR_BUCKET_NAME/*"
      ]
    }
  ]
}
```

## 5) Environment variables

Set these values in your `.env` file or environment:

```env
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_STORAGE_BUCKET_NAME=your_bucket_name
AWS_S3_REGION_NAME=your_region
```

If you use custom endpoint or CloudFront later, add those separately.

## 6) Django settings

Make sure `django-storages` is installed and added to Django only when S3 variables exist.

Example `config/settings/local.py`:

```python
AWS_STORAGE_BUCKET_NAME = os.environ.get("AWS_STORAGE_BUCKET_NAME")
AWS_ACCESS_KEY_ID = os.environ.get("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.environ.get("AWS_SECRET_ACCESS_KEY")

if AWS_STORAGE_BUCKET_NAME and AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY:
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
```

## 7) Storage classes

Create storage backends in `apps/accounts/storage.py`.

Example:

```python
from storages.backends.s3boto3 import S3Boto3Storage


class PublicMediaStorage(S3Boto3Storage):
	location = "public"
	default_acl = None
	querystring_auth = False


class PrivateMediaStorage(S3Boto3Storage):
	location = "private"
	default_acl = None
	querystring_auth = True
```

Notes:

- `location = "public"` means files are stored under `public/` in the bucket.
- `querystring_auth = False` means the returned URL is a normal URL, not a signed one.
- `querystring_auth = True` means URLs are signed and time-limited.
- `default_acl = None` avoids ACL errors on buckets that use Object Ownership.

## 8) Upload view

For a normal server-side upload, you can save to S3 from Django like this:

```python
from django.core.files.storage import storages
from django.utils.text import get_valid_filename
import os

def upload_file(upload, user_id):
    filename = get_valid_filename(os.path.basename(upload.name))
    path = f"profiles/{user_id}/{filename}"
    storage = storages["public"]
    saved_name = storage.save(path, upload)
    url = storage.url(saved_name)
    return saved_name, url
```

Important:

- Do not prefix the path with `public/` when using `storages["public"]` because the storage backend already adds that location.
- If you upload through the server, the request can be slow because Django proxies the file to S3.

## 9) Better approach for large files

For faster uploads, generate a presigned POST or presigned PUT and upload directly from the browser to S3.

Server-side example:

```python
import boto3
from django.conf import settings

s3 = boto3.client(
    "s3",
    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
    region_name=settings.AWS_S3_REGION_NAME,
)

presigned = s3.generate_presigned_post(
    Bucket=settings.AWS_STORAGE_BUCKET_NAME,
    Key="public/profiles/123/avatar.png",
    ExpiresIn=3600,
)
```

Client-side flow:

1. Django returns the presigned data.
2. Browser uploads file directly to S3.
3. Django stores the final key in the database.

## 10) If you want direct browser access to uploaded files

You have two choices:

1. Make the object public with a bucket policy for the public prefix.
2. Keep the bucket private and return a presigned GET URL.

If your bucket denies ACLs, do not try to use `public-read` ACLs.

## 11) Files that usually need changes

- `requirements/base.txt` or your dependency file
- `.env`
- `config/settings/local.py`
- `config/settings/base.py` if you want S3 in all environments
- `apps/accounts/storage.py`
- `apps/accounts/views.py`
- `apps/accounts/urls.py`

## 12) Common errors

- `AccessControlListNotSupported`: bucket does not allow ACLs. Remove ACL usage and use bucket policy or presigned URLs.
- `AccessDenied` on file URL: bucket is private or public access is blocked.
- `public/public/...` key: you added `public/` in the code and the storage backend also added `public/`.

## 13) Quick checklist

1. Install `boto3` and `django-storages`.
2. Create the S3 bucket.
3. Decide private or public.
4. Configure IAM permissions.
5. Set environment variables.
6. Add Django storage settings.
7. Use `storages["public"]` or `storages["private"]`.
8. Prefer presigned uploads for faster transfers.

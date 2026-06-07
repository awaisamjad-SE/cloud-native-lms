# LMS Django Project

A learning management system built with Django, Django REST Framework, and AWS S3 for media storage.

## Project Structure

- `apps/` - Django applications
  - `accounts/` - user and profile management, authentication
  - `courses/` - course creation, lessons, thumbnails, access control
  - `enrollments/` - student enrollments and course access state
  - `payments/` - offline payment receipts, approval workflow, admin review
  - `progress/` - learning progress tracking
- `config/` - Django settings and URL configuration
- `requirements/` - dependency lists
- `PROJECT_ARCHITECTURE.md` - full architecture and workflow documentation

## Setup

1. Create and activate a Python environment:
   ```powershell
   py -3 -m venv venv
   .\venv\Scripts\Activate.ps1
   ```

2. Install dependencies:
   ```powershell
   pip install -r requirements/base.txt
   ```

3. Configure environment variables in `.env` or your environment. Required settings include:
   - `DJANGO_SECRET_KEY`
   - `DEBUG` (`True` or `False`)
   - `DATABASE_URL` or local SQLite default
   - `AWS_ACCESS_KEY_ID`
   - `AWS_SECRET_ACCESS_KEY`
   - `AWS_STORAGE_BUCKET_NAME`
   - `AWS_S3_REGION_NAME`
   - `AWS_S3_CUSTOM_DOMAIN` (optional)
   - `AWS_S3_SIGNATURE_VERSION` (optional)
   - `AWS_S3_OBJECT_PARAMETERS` (optional)

4. Apply migrations:
   ```powershell
   py manage.py migrate
   ```

5. Create a superuser:
   ```powershell
   py manage.py createsuperuser
   ```

## Running

Start the development server:

```powershell
py manage.py runserver
```

## Testing

Run the Django test suite for all apps:

```powershell
py manage.py test
```

Run specific tests:

```powershell
py manage.py test apps.payments.tests
py manage.py test apps.courses.tests
```

## AWS S3 Upload and URL Behavior

- Public files (course thumbnails, profile images, preview lessons) are stored in a public S3 location and exposed via a full URL.
- Private files (paid lesson videos, payment receipts) are accessed through region-aware presigned URLs.
- The project includes region detection logic to prevent `AuthorizationQueryParametersError` when bucket region and signed URL region mismatch.

## Notes

- The `PROJECT_ARCHITECTURE.md` file contains detailed architecture, app responsibilities, API flows, and troubleshooting.
- Use thumbnails and optimized media to reduce load time.
- For production, consider adding a CDN like CloudFront in front of S3.

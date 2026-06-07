# LMS Project Architecture & Workflow Documentation

## Project Overview

This is a **Learning Management System (LMS)** built with Django REST Framework, featuring course management, student enrollments, payment processing, and lesson progress tracking. All file uploads (images, videos, documents) are stored on AWS S3 with full URLs returned in API responses.

---

## Overall Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Frontend (Client App)                     │
│                   (React / Vue / etc.)                       │
└────────────────────────┬────────────────────────────────────┘
                         │ API Calls
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              Django REST API (http://localhost:8000/api/v1)  │
│                                                              │
│  ┌──────────┐  ┌────────────┐  ┌────────────┐ ┌──────────┐ │
│  │ Accounts │  │  Courses   │  │ Enrollments│ │Payments  │ │
│  │   App    │  │    App     │  │    App     │ │   App    │ │
│  └──────────┘  └────────────┘  └────────────┘ └──────────┘ │
│                                                              │
│  ┌──────────┐                                               │
│  │ Progress │                                               │
│  │   App    │                                               │
│  └──────────┘                                               │
└─────────────────────────────┬───────────────────────────────┘
                              │
                    ┌─────────┴──────────┐
                    ▼                    ▼
            ┌──────────────┐      ┌──────────────┐
            │  PostgreSQL  │      │  AWS S3      │
            │   Database   │      │  Storage     │
            └──────────────┘      └──────────────┘
```

---

## Database Schema (Key Entities)

### User (Accounts App)
- **Fields**: id (UUID), username, email, password, role (admin/student), is_staff, is_active, is_email_verified
- **Purpose**: Authentication & authorization

### UserProfile (Accounts App)
- **Fields**: user (FK), profile_image (CharField, stores S3 key), phone_number, bio
- **Purpose**: Stores user metadata & profile picture

### Course
- **Fields**: id, title, slug, description, thumbnail (S3 key), price, category, status (draft/published/archived), is_featured, created_by (FK to User), created_at, updated_at
- **Purpose**: Defines course content & metadata

### Lesson
- **Fields**: id, course (FK), title, description, lesson_type (video/document), s3_key (full S3 path), is_preview (bool), order, duration, created_at
- **Purpose**: Individual course units/modules

### Enrollment
- **Fields**: id, student (FK to User), course (FK), is_active (bool), created_at
- **Purpose**: Links students to purchased/enrolled courses

### Payment
- **Fields**: id, student (FK), course (FK), amount, bank_account (FK), proof_receipt (S3 key), transaction_reference, proof_note, status (pending/approved/rejected), approved_by (FK), approved_at, rejection_reason, created_at, updated_at
- **Purpose**: Offline payment tracking for course purchases

### BankAccount
- **Fields**: id, bank_name, account_title, account_number, iban, instructions, is_active, created_at
- **Purpose**: Admin-configured bank details for student payments

---

## Key Features & Implementation

### 1. **Course Access Control (Who Can See What)**

#### Public/Student View (Everyone)
- Can see **only PUBLISHED courses** in `GET /api/v1/courses/`
- Can view published course details `GET /api/v1/courses/{slug}/`
- Can see lesson list for published courses `GET /api/v1/courses/{slug}/lessons/`

#### Preview Lessons (Free Access)
- Lessons with `is_preview=true` are **publicly accessible**
- Returns a public S3 URL (no auth required) in `GET /api/v1/lessons/{id}/access/`

#### Paid Lessons (Enrollment Required)
- Lessons with `is_preview=false` require:
  1. User must be **authenticated**
  2. User must have **active enrollment** in the course
  3. Returns a presigned private S3 URL (signed for 1 hour) in `GET /api/v1/lessons/{id}/access/`

#### Admin View (Staff/Admin Role)
- Can see **ALL courses** (draft, published, archived) in `GET /api/v1/courses/`
- Can create, update, publish courses in `/admin/courses/` endpoints
- Can access student payment receipts (private S3 URLs) in `GET /api/v1/admin/payments/`

**Code Location**: [apps/courses/views.py](apps/courses/views.py) - `_is_course_admin()` helper & `CourseCatalogView`, `CourseDetailView`

---

### 2. **Course Purchase & Enrollment Flow**

```
STUDENT PURCHASE FLOW:
  
  1. Student browses published courses → GET /api/v1/courses/
  
  2. Student clicks "Buy Course" → Views payment details
     GET /api/v1/payments/bank-accounts/ (public, unauth required)
  
  3. Student submits offline payment proof:
     POST /api/v1/payments/offline/submit/
     - Uploads receipt image/PDF to private S3
     - Creates Payment record with status=PENDING
  
  4. Admin reviews payment:
     GET /api/v1/admin/payments/
     - Sees student name, course, receipt URL (signed)
     - Admin can open receipt image in browser
  
  5. Admin approves payment:
     POST /api/v1/admin/payments/{id}/approve/
     - Marks payment status=APPROVED
     - Creates Enrollment record (is_active=true)
     - Student now has access to paid lessons
  
  6. Student accesses course lessons:
     GET /api/v1/enrollments/my/
     - Sees purchased courses
     - GET /api/v1/courses/{slug}/lessons/
     - Paid lessons show locked=false (because enrollment.is_active=true)
  
  7. Student views lesson content:
     GET /api/v1/lessons/{id}/access/
     - Returns presigned S3 URL (1-hour validity)
     - Frontend can stream video/download document
```

**Code Locations**:
- Submit payment: [apps/payments/views.py](apps/payments/views.py) - `OfflinePaymentSubmitView`
- Admin approval: [apps/payments/views.py](apps/payments/views.py) - `AdminPaymentApproveView`
- Enrollment check: [apps/courses/views.py](apps/courses/views.py) - `LessonAccessView`

---

### 3. **File Upload & Storage**

All uploaded files are stored on **AWS S3** with full URLs returned in API responses.

#### Profile Image Upload
- **Endpoint**: `POST /api/v1/auth/profile/upload-image/`
- **Storage**: `public/profiles/{user_id}/filename.jpg`
- **Response**: Returns full S3 URL in `profile_image` field
- **Size Limit**: 5 MB

#### Course Thumbnail Upload
- **Endpoint**: `POST /api/v1/admin/courses/{id}/thumbnail/`
- **Storage**: `public/thumbnails/{course_slug}/filename.jpg`
- **Response**: Returns full S3 URL in `thumbnail` field
- **Size Limit**: 5 MB

#### Lesson Media Upload (Video/Document)
- **Endpoint**: `POST /api/v1/admin/lessons/`
- **Storage**: 
  - Preview: `public/previews/filename.mp4`
  - Paid: `private/videos/filename.mp4` or `private/documents/filename.pdf`
- **Response**: Returns full S3 URL in `url` field
- **Size Limit**: 20 MB

#### Payment Receipt Upload
- **Endpoint**: `POST /api/v1/payments/offline/submit/`
- **Storage**: `private/payment-proofs/{student_id}/{course_id}/filename.pdf`
- **Response**: Returns presigned S3 URL in `proof_receipt_url` field
- **Size Limit**: 20 MB

**Code Locations**:
- Storage backends: [apps/accounts/storage.py](apps/accounts/storage.py)
- URL generation: [apps/payments/serializers.py](apps/payments/serializers.py) - `get_private_url_from_key()`

---

## App-by-App Breakdown

### **1. Accounts App** (`apps/accounts/`)
**Purpose**: User registration, authentication, profile management

**Key Models**:
- `User`: Django AbstractUser with UUID PK, role field, email verification flag
- `UserProfile`: OneToOne with User, stores profile_image, phone_number, bio

**Key Endpoints**:
| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/auth/register/` | User signup |
| POST | `/auth/login/` | Get JWT tokens (access + refresh) |
| GET | `/auth/profile/` | Get authenticated user profile |
| PATCH | `/auth/profile/` | Update user bio, phone, name |
| POST | `/auth/profile/upload-image/` | Upload profile picture to S3 |
| POST | `/auth/change-password/` | Change user password |
| GET | `/auth/admin/users/` | List all users (admin only) |
| POST | `/auth/admin/users/{id}/activate/` | Enable/disable user (admin) |

**Authentication**: JWT (access token in Authorization header)

**Response Example** (Login):
```json
{
  "access": "eyJ0eXAi...",
  "refresh": "eyJ0eXAi...",
  "user": {
    "id": "3cdcdf52-...",
    "username": "student1",
    "email": "student1@example.com",
    "role": "student",
    "profile_image": "https://my-bucket.s3.amazonaws.com/public/profiles/3cdcdf52-/image.jpg",
    "phone_number": "+1234567890",
    "bio": "Learning web development"
  }
}
```

---

### **2. Courses App** (`apps/courses/`)
**Purpose**: Course management, lesson organization, content delivery

**Key Models**:
- `Course`: Title, description, thumbnail, price, status (draft/published/archived), category
- `Lesson`: Belongs to Course, has s3_key (S3 path), lesson_type (video/document), is_preview flag, order

**Key Endpoints**:
| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/courses/` | List published courses (or all if admin) |
| GET | `/courses/{slug}/` | Get course detail + lessons |
| GET | `/courses/{slug}/lessons/` | Get lessons (with locked flag) |
| GET | `/lessons/{id}/access/` | Get S3 URL to view/download lesson |
| POST | `/admin/courses/` | Create course (admin) |
| PATCH | `/admin/courses/{id}/` | Update course (admin) |
| POST | `/admin/courses/{id}/publish/` | Publish draft course (admin) |
| POST | `/admin/courses/{id}/thumbnail/` | Upload course thumbnail (admin) |
| POST | `/admin/lessons/` | Create lesson + upload media (admin) |

**Access Control**:
- Public courses (PUBLISHED): Anyone can see
- Draft/Archived courses: Admin only
- Preview lessons: Public access to S3 URL
- Paid lessons: Requires active enrollment

**Response Example** (Course List):
```json
[
  {
    "id": 1,
    "title": "Python Fundamentals",
    "slug": "python-course",
    "price": "1000.00",
    "category": "Programming",
    "thumbnail_url": "https://my-bucket.s3.amazonaws.com/public/thumbnails/python-course/thumb.jpg",
    "is_featured": true
  }
]
```

---

### **3. Enrollments App** (`apps/enrollments/`)
**Purpose**: Track student-to-course relationships

**Key Models**:
- `Enrollment`: Links student (User) to course, has is_active flag

**Key Endpoints**:
| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/enrollments/my/` | Get student's enrolled courses |
| GET | `/admin/enrollments/` | List all enrollments (admin) |
| POST | `/admin/enrollments/` | Create enrollment manually (admin) |
| POST | `/admin/enrollments/{id}/activate/` | Re-enable enrollment (admin) |
| POST | `/admin/enrollments/{id}/deactivate/` | Suspend enrollment (admin) |

**How Enrollment Affects Access**:
- When `Enrollment.is_active=true`, student can access paid lessons
- When approval happens (payment approved), enrollment is created automatically
- Admin can manually enroll students without payment

---

### **4. Payments App** (`apps/payments/`)
**Purpose**: Track offline course purchases

**Key Models**:
- `BankAccount`: Admin-configured bank details (name, account #, IBAN, instructions)
- `Payment`: Links student, course, bank account; stores proof_receipt (S3 key), status, approval info

**Key Endpoints**:
| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/payments/bank-accounts/` | List active bank accounts (public) |
| POST | `/payments/offline/submit/` | Student submits payment proof |
| GET | `/payments/my/` | Student sees own payments |
| GET | `/admin/payments/` | List all payments (admin) |
| POST | `/admin/payments/{id}/approve/` | Approve payment + create enrollment (admin) |
| POST | `/admin/payments/{id}/reject/` | Reject payment + set reason (admin) |
| GET/POST | `/admin/bank-accounts/` | CRUD bank accounts (admin) |

**Payment Status Flow**:
```
Student Submits → PENDING 
                    ↓
              Admin Reviews Receipt
                    ↓
              APPROVED → Enrollment created, student gets access
              REJECTED → Reason stored, student must resubmit
```

**Response Example** (Payment Detail):
```json
{
  "id": 4,
  "student": "f39d7da1-bcd7-...",
  "course": 3,
  "amount": "1000.00",
  "bank_account": { "id": 1, "bank_name": "HBL", ... },
  "proof_receipt": "https://my-bucket.s3.amazonaws.com/private/payment-proofs/.../receipt.pdf?X-Amz-Signature=...",
  "proof_receipt_url": "https://my-bucket.s3.amazonaws.com/private/payment-proofs/.../receipt.pdf?X-Amz-Signature=...",
  "transaction_reference": "TXN-123",
  "status": "pending",
  "approved_by": null,
  "approved_at": null
}
```

---

### **5. Progress App** (`apps/progress/`)
**Purpose**: Track student lesson completion

**Key Models**:
- `LessonProgress`: Stores student, lesson, completed_at timestamp

**Key Endpoints**:
| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/lessons/{id}/complete/` | Mark lesson as complete (student) |
| GET | `/courses/{slug}/progress/` | Get student's progress in course |

**Progress Tracking**:
- Student clicks "Mark Complete" after watching/downloading lesson
- Admin can view course progress by student (e.g., 3/10 lessons completed)

---

## Security & Permissions

### Authentication
- **JWT Tokens** (via SimpleJWT)
- Access token expires: 1 hour
- Refresh token expires: 7 days
- All protected endpoints require `Authorization: Bearer {access_token}`

### Authorization (Per-Endpoint)
| Endpoint Type | Required Permission | Logic |
|---------------|-------------------|-------|
| Public courses/lessons | None | Anyone can see PUBLISHED courses & preview lessons |
| Student endpoints | IsAuthenticated | Must have valid JWT token |
| Paid lesson access | IsAuthenticated + Enrollment | Must be enrolled & enrollment.is_active=true |
| Admin endpoints | IsAuthenticated + (is_staff or role="admin") | Only staff/admin users |
| Presigned URLs | Signed query params | Valid for 1 hour, region-specific |

### File Upload Security
- **Public files** (profiles, thumbnails, previews): No signature required, anyone can access
- **Private files** (videos, documents, receipts): Presigned URLs required, expire in 1 hour
- **Size limits**: 5 MB (images), 20 MB (videos/documents/receipts)
- **Region handling**: S3 bucket region is auto-detected for correct URL signing

---

## Workflow Diagrams

### Student Onboarding to Course Access
```
┌──────────────┐
│  New Student │
└───────┬──────┘
        │
        ▼
┌─────────────────────────┐
│  POST /auth/register/   │
│  (username, email, pwd) │
└───────┬─────────────────┘
        │
        ▼
┌──────────────────────┐
│ User created         │
│ JWT tokens issued    │
└───────┬──────────────┘
        │
        ▼
┌──────────────────────────┐
│  GET /courses/           │
│  (Browse published)      │
└───────┬──────────────────┘
        │
        ▼
┌──────────────────────────┐
│  GET /lessons/{id}/      │
│  access/                 │
│  (Preview = public URL)  │
└───────┬──────────────────┘
        │
        ▼
┌──────────────────────────────┐
│  Wants to buy → Click "Buy"  │
└───────┬──────────────────────┘
        │
        ▼
┌──────────────────────────────┐
│  GET /payments/bank-accounts │
│  (See payment instructions)  │
└───────┬──────────────────────┘
        │
        ▼
┌─────────────────────────────────────┐
│  POST /payments/offline/submit/      │
│  (Upload receipt image to S3)        │
└───────┬─────────────────────────────┘
        │
        ▼
┌──────────────────────────┐
│  Payment: PENDING        │
│  (Awaiting admin review) │
└───────┬──────────────────┘
        │
  (24-48 hours later)
        │
        ▼
┌────────────────────────────────────┐
│  Admin: POST /admin/payments/      │
│         {id}/approve/              │
│  (Enrollment created)              │
└───────┬────────────────────────────┘
        │
        ▼
┌────────────────────────────────┐
│  Student: GET /enrollments/my/ │
│  (Course now appears)          │
└───────┬────────────────────────┘
        │
        ▼
┌──────────────────────────────────┐
│  GET /lessons/{id}/access/       │
│  (Paid lesson = presigned URL)   │
└────────────────────────────────┘
```

---

## Configuration & Environment

### Key Settings
- `DEBUG`: True (local.py), False (production.py)
- `AWS_STORAGE_BUCKET_NAME`: S3 bucket name
- `AWS_S3_REGION_NAME`: Bucket region (default: us-east-1)
- `AWS_QUERYSTRING_AUTH`: True (presigned URLs required for private files)
- `COURSE_PRESIGNED_EXPIRES`: 3600 seconds (1 hour)
- `PRIVATE_URL_EXPIRES`: 3600 seconds (1 hour)

### Database
- **Local**: SQLite (db.sqlite3)
- **Production**: PostgreSQL (recommended)

### Storage
- **Local**: Filesystem (media/ folder)
- **Production**: AWS S3 (public + private buckets)

---

## Testing

Run all tests:
```bash
python manage.py test
```

Run app-specific tests:
```bash
python manage.py test apps.courses
python manage.py test apps.payments
python manage.py test apps.accounts
```

Run single test:
```bash
python manage.py test apps.payments.tests.PaymentFlowTests.test_student_offline_submission_creates_pending_payment
```

---

## Common API Usage Examples

### Login & Get Access Token
```bash
curl -X POST http://localhost:8000/api/v1/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username": "student1", "password": "pass123"}'
```

### Browse Published Courses
```bash
curl http://localhost:8000/api/v1/courses/
```

### View Lesson (Public/Paid)
```bash
curl -H "Authorization: Bearer {access_token}" \
  http://localhost:8000/api/v1/lessons/7/access/
```

### Submit Payment Proof
```bash
curl -X POST http://localhost:8000/api/v1/payments/offline/submit/ \
  -H "Authorization: Bearer {access_token}" \
  -F "course_id=3" \
  -F "bank_account_id=1" \
  -F "proof_receipt=@receipt.pdf"
```

### Admin Approve Payment
```bash
curl -X POST http://localhost:8000/api/v1/admin/payments/4/approve/ \
  -H "Authorization: Bearer {admin_token}"
```

---

## Troubleshooting

### "Lesson not available" Error
- Course status is not PUBLISHED (check admin panel)
- Only admins can access non-published courses

### "Purchase course first" Error
- Student tried to access paid lesson without active enrollment
- Verify payment was approved and enrollment was created

### S3 URL Returns 403 Forbidden
- Presigned URL expired (valid for 1 hour only)
- Generate a fresh URL by calling `/lessons/{id}/access/` again

### Receipt Image Won't Load
- S3 bucket permissions: Verify ACLs and bucket policy
- Region mismatch: Auto-detected; if issue persists, check `AWS_S3_REGION_NAME`

---

## Future Enhancements

- [ ] Refund system for approved payments
- [ ] Course completion certificates
- [ ] Student performance analytics
- [ ] Bulk course/lesson upload
- [ ] Course reviews & ratings
- [ ] Group learning (cohorts)
- [ ] Live video sessions
- [ ] Email notifications
- [ ] Two-factor authentication

---

**Document Version**: 1.0  
**Last Updated**: June 7, 2026  
**Author**: LMS Development Team

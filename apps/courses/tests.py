from unittest.mock import MagicMock, patch

from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth import get_user_model
from django.test import override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.courses.models import Course, Lesson
from apps.enrollments.models import Enrollment

User = get_user_model()


class CourseApiTests(APITestCase):
	def setUp(self):
		self.admin = User.objects.create_user(
			username="admin_courses",
			email="admin_courses@example.com",
			password="adminpass",
			role="admin",
			is_staff=True,
		)
		self.student = User.objects.create_user(
			username="student_courses",
			email="student_courses@example.com",
			password="studentpass",
			role="student",
		)
		self.published_course = Course.objects.create(
			title="Published Python",
			slug="published-python",
			price=1200,
			status=Course.Status.PUBLISHED,
			created_by=self.admin,
		)
		self.draft_course = Course.objects.create(
			title="Draft Django",
			slug="draft-django",
			price=800,
			status=Course.Status.DRAFT,
			created_by=self.admin,
		)
		self.preview_lesson = Lesson.objects.create(
			course=self.published_course,
			title="Intro",
			lesson_type=Lesson.LessonType.VIDEO,
			s3_key="public/previews/intro.mp4",
			is_preview=True,
			order=1,
			duration=120,
		)
		self.paid_lesson = Lesson.objects.create(
			course=self.published_course,
			title="Advanced",
			lesson_type=Lesson.LessonType.VIDEO,
			s3_key="private/videos/advanced.mp4",
			is_preview=False,
			order=2,
			duration=300,
		)

	def test_catalog_lists_only_published_courses(self):
		response = self.client.get(reverse("courses:course_catalog"))
		self.assertEqual(response.status_code, status.HTTP_200_OK)
		slugs = [item["slug"] for item in response.data]
		self.assertIn(self.published_course.slug, slugs)
		self.assertNotIn(self.draft_course.slug, slugs)

	def test_admin_catalog_lists_draft_and_published_courses(self):
		self.client.login(username="admin_courses", password="adminpass")
		response = self.client.get(reverse("courses:course_catalog"))

		self.assertEqual(response.status_code, status.HTTP_200_OK)
		slugs = [item["slug"] for item in response.data]
		self.assertIn(self.published_course.slug, slugs)
		self.assertIn(self.draft_course.slug, slugs)

	def test_admin_can_retrieve_draft_course_detail(self):
		self.client.login(username="admin_courses", password="adminpass")
		url = reverse("courses:course_detail", kwargs={"slug": self.draft_course.slug})
		response = self.client.get(url)

		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.assertEqual(response.data["slug"], self.draft_course.slug)
		self.assertEqual(response.data["status"], self.draft_course.status)

	def test_lessons_endpoint_marks_paid_lesson_locked_for_anonymous(self):
		url = reverse("courses:course_lessons", kwargs={"slug": self.published_course.slug})
		response = self.client.get(url)

		self.assertEqual(response.status_code, status.HTTP_200_OK)
		by_title = {item["title"]: item for item in response.data}
		self.assertFalse(by_title["Intro"]["locked"])
		self.assertTrue(by_title["Advanced"]["locked"])

	@patch("apps.courses.views._public_url_for_key", return_value="https://example.com/intro.mp4")
	def test_preview_lesson_access_returns_public_url(self, _):
		url = reverse("courses:lesson_access", kwargs={"pk": self.preview_lesson.id})
		response = self.client.get(url)

		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.assertEqual(response.data["preview"], True)
		self.assertEqual(response.data["url"], "https://example.com/intro.mp4")

	def test_paid_lesson_access_requires_authentication(self):
		url = reverse("courses:lesson_access", kwargs={"pk": self.paid_lesson.id})
		response = self.client.get(url)
		self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

	@patch("apps.courses.serializers.storages")
	def test_admin_preview_video_create_with_file_returns_public_key(self, mock_storages):
		self.client.login(username="admin_courses", password="adminpass")

		mock_public_storage = MagicMock()
		mock_public_storage.save.return_value = "previews/lesson1.mp4"
		mock_public_storage.url.return_value = "https://example.com/public/previews/lesson1.mp4"
		mock_private_storage = MagicMock()
		mock_storages.__getitem__.side_effect = lambda name: {
			"public": mock_public_storage,
			"private": mock_private_storage,
		}[name]

		upload = SimpleUploadedFile("lesson1.mp4", b"video-bytes", content_type="video/mp4")
		url = reverse("courses:admin_lesson_create")
		response = self.client.post(
			url,
			data={
				"course": self.published_course.id,
				"title": "Lesson 1",
				"lesson_type": Lesson.LessonType.VIDEO,
				"is_preview": True,
				"order": 3,
				"duration": 120,
				"file": upload,
			},
		)

		self.assertEqual(response.status_code, status.HTTP_201_CREATED)
		self.assertEqual(response.data["course"], self.published_course.id)
		self.assertEqual(response.data["key"], "public/previews/lesson1.mp4")
		self.assertEqual(response.data["s3_key"], "public/previews/lesson1.mp4")
		self.assertEqual(response.data["url"], "https://example.com/public/previews/lesson1.mp4")
		mock_public_storage.save.assert_called_once()

	@patch("apps.courses.serializers.storages")
	def test_admin_document_create_with_file_returns_private_key(self, mock_storages):
		self.client.login(username="admin_courses", password="adminpass")

		mock_public_storage = MagicMock()
		mock_private_storage = MagicMock()
		mock_private_storage.save.return_value = "documents/chapter1.pdf"
		mock_private_storage.url.return_value = "https://signed.example.com/private/documents/chapter1.pdf"
		mock_storages.__getitem__.side_effect = lambda name: {
			"public": mock_public_storage,
			"private": mock_private_storage,
		}[name]

		upload = SimpleUploadedFile("chapter1.pdf", b"pdf-bytes", content_type="application/pdf")
		url = reverse("courses:admin_lesson_create")
		response = self.client.post(
			url,
			data={
				"course": self.published_course.id,
				"title": "Lesson 2",
				"lesson_type": Lesson.LessonType.DOCUMENT,
				"is_preview": False,
				"order": 4,
				"duration": 180,
				"file": upload,
			},
		)

		self.assertEqual(response.status_code, status.HTTP_201_CREATED)
		self.assertEqual(response.data["course"], self.published_course.id)
		self.assertEqual(response.data["s3_key"], "private/documents/chapter1.pdf")
		self.assertEqual(response.data["url"], "https://signed.example.com/private/documents/chapter1.pdf")
		mock_private_storage.save.assert_called_once()

	@patch("apps.courses.serializers.storages")
	def test_admin_lesson_upload_rejects_files_over_20mb(self, mock_storages):
		self.client.login(username="admin_courses", password="adminpass")

		mock_public_storage = MagicMock()
		mock_private_storage = MagicMock()
		mock_storages.__getitem__.side_effect = lambda name: {
			"public": mock_public_storage,
			"private": mock_private_storage,
		}[name]

		upload = SimpleUploadedFile(
			"big-video.mp4",
			b"0" * (20 * 1024 * 1024 + 1),
			content_type="video/mp4",
		)
		url = reverse("courses:admin_lesson_create")
		response = self.client.post(
			url,
			data={
				"course": self.published_course.id,
				"title": "Large Lesson",
				"lesson_type": Lesson.LessonType.VIDEO,
				"is_preview": True,
				"order": 5,
				"duration": 600,
				"file": upload,
			},
		)

		self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
		self.assertIn("file", response.data)

	@override_settings(AWS_STORAGE_BUCKET_NAME="test-bucket")
	@patch("apps.courses.views.boto3.client")
	def test_paid_lesson_access_returns_presigned_url_for_enrolled_user(self, mock_boto_client):
		Enrollment.objects.create(student=self.student, course=self.published_course, is_active=True)

		mock_client = MagicMock()
		mock_client.generate_presigned_url.return_value = "https://signed.example.com/private-object"
		mock_boto_client.return_value = mock_client

		self.client.login(username="student_courses", password="studentpass")
		url = reverse("courses:lesson_access", kwargs={"pk": self.paid_lesson.id})
		response = self.client.get(url)

		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.assertEqual(response.data["preview"], False)
		self.assertIn("url", response.data)
		mock_client.generate_presigned_url.assert_called_once()

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.courses.models import Course, Lesson
from apps.enrollments.models import Enrollment
from .models import LessonProgress

User = get_user_model()


class ProgressApiTests(APITestCase):
	def setUp(self):
		self.admin = User.objects.create_user(
			username="admin_progress",
			email="admin_progress@example.com",
			password="adminpass",
			role="admin",
			is_staff=True,
		)
		self.student = User.objects.create_user(
			username="student_progress",
			email="student_progress@example.com",
			password="studentpass",
			role="student",
		)
		self.course = Course.objects.create(
			title="Progress Course",
			slug="progress-course",
			price=3000,
			status=Course.Status.PUBLISHED,
			created_by=self.admin,
		)
		self.preview_lesson = Lesson.objects.create(
			course=self.course,
			title="Preview Lesson",
			lesson_type=Lesson.LessonType.VIDEO,
			s3_key="public/previews/preview.mp4",
			is_preview=True,
			order=1,
			duration=60,
		)
		self.paid_lesson = Lesson.objects.create(
			course=self.course,
			title="Paid Lesson",
			lesson_type=Lesson.LessonType.VIDEO,
			s3_key="private/videos/paid.mp4",
			is_preview=False,
			order=2,
			duration=180,
		)

	def test_student_can_complete_preview_lesson_without_enrollment(self):
		self.client.login(username="student_progress", password="studentpass")
		url = reverse("progress:lesson_complete", kwargs={"pk": self.preview_lesson.id})
		response = self.client.post(url)

		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.assertTrue(LessonProgress.objects.filter(student=self.student, lesson=self.preview_lesson, is_completed=True).exists())

	def test_student_cannot_complete_paid_lesson_without_enrollment(self):
		self.client.login(username="student_progress", password="studentpass")
		url = reverse("progress:lesson_complete", kwargs={"pk": self.paid_lesson.id})
		response = self.client.post(url)

		self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

	def test_course_progress_reflects_completed_lessons(self):
		Enrollment.objects.create(student=self.student, course=self.course, is_active=True)
		self.client.login(username="student_progress", password="studentpass")

		complete_preview_url = reverse("progress:lesson_complete", kwargs={"pk": self.preview_lesson.id})
		complete_paid_url = reverse("progress:lesson_complete", kwargs={"pk": self.paid_lesson.id})
		progress_url = reverse("progress:course_progress", kwargs={"slug": self.course.slug})

		self.client.post(complete_preview_url)
		self.client.post(complete_paid_url)
		response = self.client.get(progress_url)

		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.assertEqual(response.data["total_lessons"], 2)
		self.assertEqual(response.data["completed_lessons"], 2)
		self.assertEqual(response.data["completion_percent"], 100.0)

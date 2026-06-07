from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.courses.models import Course
from .models import Enrollment

User = get_user_model()


class EnrollmentApiTests(APITestCase):
	def setUp(self):
		self.admin = User.objects.create_user(
			username="admin",
			email="admin@example.com",
			password="adminpass",
			role="admin",
			is_staff=True,
		)
		self.student = User.objects.create_user(
			username="student",
			email="student@example.com",
			password="studentpass",
			role="student",
		)
		self.other_student = User.objects.create_user(
			username="other",
			email="other@example.com",
			password="otherpass",
			role="student",
		)
		self.course = Course.objects.create(
			title="Python Mastery",
			slug="python-mastery",
			price=2000,
			status=Course.Status.PUBLISHED,
			created_by=self.admin,
		)

	def test_student_can_list_own_active_enrollments(self):
		Enrollment.objects.create(student=self.student, course=self.course, is_active=True)
		Enrollment.objects.create(student=self.other_student, course=self.course, is_active=True)

		self.client.login(username="student", password="studentpass")
		url = reverse("enrollments:my_enrollments")
		response = self.client.get(url)

		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.assertEqual(len(response.data), 1)
		self.assertEqual(str(response.data[0]["student"]), str(self.student.id))

	def test_admin_can_create_enrollment(self):
		self.client.login(username="admin", password="adminpass")
		url = reverse("enrollments:admin_enrollments")
		payload = {"student_id": str(self.student.id), "course_id": self.course.id}

		response = self.client.post(url, payload, format="json")

		self.assertEqual(response.status_code, status.HTTP_201_CREATED)
		self.assertTrue(Enrollment.objects.filter(student=self.student, course=self.course, is_active=True).exists())

	def test_non_admin_cannot_create_enrollment(self):
		self.client.login(username="student", password="studentpass")
		url = reverse("enrollments:admin_enrollments")
		payload = {"student_id": str(self.other_student.id), "course_id": self.course.id}

		response = self.client.post(url, payload, format="json")

		self.assertIn(response.status_code, (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN))

	def test_admin_can_activate_and_deactivate_enrollment(self):
		enrollment = Enrollment.objects.create(student=self.student, course=self.course, is_active=True)
		self.client.login(username="admin", password="adminpass")

		deactivate_url = reverse("enrollments:admin_enrollment_deactivate", kwargs={"pk": enrollment.id})
		activate_url = reverse("enrollments:admin_enrollment_activate", kwargs={"pk": enrollment.id})

		deactivate_response = self.client.post(deactivate_url)
		enrollment.refresh_from_db()
		self.assertEqual(deactivate_response.status_code, status.HTTP_200_OK)
		self.assertFalse(enrollment.is_active)

		activate_response = self.client.post(activate_url)
		enrollment.refresh_from_db()
		self.assertEqual(activate_response.status_code, status.HTTP_200_OK)
		self.assertTrue(enrollment.is_active)

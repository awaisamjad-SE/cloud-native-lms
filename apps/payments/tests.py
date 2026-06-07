from unittest.mock import MagicMock, patch

from django.test import override_settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.courses.models import Course
from apps.enrollments.models import Enrollment
from .models import BankAccount, Payment

User = get_user_model()


class PaymentFlowTests(APITestCase):
	def setUp(self):
		self.admin = User.objects.create_user(
			username="admin_payments",
			email="admin_payments@example.com",
			password="adminpass",
			role="admin",
			is_staff=True,
		)
		self.student = User.objects.create_user(
			username="student_payments",
			email="student_payments@example.com",
			password="studentpass",
			role="student",
		)
		self.course = Course.objects.create(
			title="Payment Course",
			slug="payment-course",
			price=2500,
			status=Course.Status.PUBLISHED,
			created_by=self.admin,
		)
		self.bank = BankAccount.objects.create(
			bank_name="Sample Bank",
			account_title="LMS Pvt",
			account_number="1234567890",
			iban="PK00TEST000000",
			instructions="Transfer then share reference",
			is_active=True,
		)

	def test_student_offline_submission_creates_pending_payment(self):
		self.client.login(username="student_payments", password="studentpass")
		url = reverse("payments:offline_payment_submit")
		payload = {
			"course_id": self.course.id,
			"bank_account_id": self.bank.id,
			"transaction_reference": "TXN-1001",
			"proof_note": "Paid via bank transfer",
		}

		response = self.client.post(url, payload, format="json")

		self.assertEqual(response.status_code, status.HTTP_201_CREATED)
		payment = Payment.objects.get(id=response.data["id"])
		self.assertEqual(payment.status, Payment.Status.PENDING)
		self.assertEqual(payment.student, self.student)
		self.assertEqual(payment.course, self.course)

	@patch("apps.payments.serializers.storages")
	@patch("apps.payments.serializers.boto3")
	@patch("apps.payments.views.storages")
	def test_student_offline_submission_accepts_proof_receipt_file(self, mock_storages_views, mock_boto3_serializers, mock_storages_serializers):
		self.client.login(username="student_payments", password="studentpass")
		
		# Mock the storage in the views module (where the file is saved)
		mock_private_storage = MagicMock()
		mock_private_storage.save.return_value = "payment-proofs/1/1/receipt.pdf"
		mock_storages_views.__getitem__.return_value = mock_private_storage
		
		# Mock the storage in the serializers module (where the URL is generated)
		mock_serializer_storage = MagicMock()
		mock_serializer_storage.url.return_value = "https://example.com/private/payment-proofs/1/1/receipt.pdf"
		mock_storages_serializers.__getitem__.return_value = mock_serializer_storage
		
		# Mock boto3 in the serializers module to provide presigned URL fallback
		mock_client = MagicMock()
		mock_client.get_bucket_location.return_value = {"LocationConstraint": "ap-south-1"}
		mock_client.generate_presigned_url.return_value = "https://example.com/private/payment-proofs/1/1/receipt.pdf"
		mock_boto3_serializers.client.return_value = mock_client

		receipt = SimpleUploadedFile("receipt.pdf", b"receipt-bytes", content_type="application/pdf")
		url = reverse("payments:offline_payment_submit")
		payload = {
			"course_id": self.course.id,
			"bank_account_id": self.bank.id,
			"transaction_reference": "TXN-1002",
			"proof_note": "Paid via bank transfer",
			"proof_receipt": receipt,
		}

		response = self.client.post(url, payload, format="multipart")

		self.assertEqual(response.status_code, status.HTTP_201_CREATED)
		payment = Payment.objects.get(id=response.data["id"])
		self.assertEqual(payment.proof_receipt, "private/payment-proofs/1/1/receipt.pdf")
		# proof_receipt now returns the full URL (via SerializerMethodField)
		self.assertEqual(response.data["proof_receipt"], "https://example.com/private/payment-proofs/1/1/receipt.pdf")
		# proof_receipt_key returns the raw S3 key
		self.assertEqual(response.data["proof_receipt_key"], "private/payment-proofs/1/1/receipt.pdf")
		# proof_receipt_url also returns the full URL
		self.assertEqual(response.data["proof_receipt_url"], "https://example.com/private/payment-proofs/1/1/receipt.pdf")

	def test_duplicate_pending_submission_returns_existing_payment(self):
		payment = Payment.objects.create(
			student=self.student,
			course=self.course,
			amount=self.course.price,
			bank_account=self.bank,
			transaction_reference="TXN-EXISTING",
			proof_note="Initial pending",
			status=Payment.Status.PENDING,
		)

		self.client.login(username="student_payments", password="studentpass")
		url = reverse("payments:offline_payment_submit")
		payload = {"course_id": self.course.id, "bank_account_id": self.bank.id}
		response = self.client.post(url, payload, format="json")

		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.assertEqual(response.data["payment"]["id"], payment.id)

	def test_admin_approval_creates_enrollment_and_marks_payment_approved(self):
		payment = Payment.objects.create(
			student=self.student,
			course=self.course,
			amount=self.course.price,
			bank_account=self.bank,
			transaction_reference="TXN-APPROVE",
			proof_note="Need approval",
			status=Payment.Status.PENDING,
		)

		self.client.login(username="admin_payments", password="adminpass")
		url = reverse("payments:admin_payment_approve", kwargs={"pk": payment.id})
		response = self.client.post(url, {}, format="json")

		self.assertEqual(response.status_code, status.HTTP_200_OK)
		payment.refresh_from_db()
		self.assertEqual(payment.status, Payment.Status.APPROVED)
		self.assertEqual(payment.approved_by, self.admin)
		self.assertTrue(Enrollment.objects.filter(student=self.student, course=self.course, is_active=True).exists())

	@override_settings(AWS_STORAGE_BUCKET_NAME="test-bucket", AWS_S3_REGION_NAME="ap-south-1")
	@patch("apps.payments.serializers.storages")
	@patch("apps.payments.serializers.boto3")
	def test_payment_serializer_falls_back_to_region_aware_presigned_url(self, mock_boto3_module, mock_storages):
		self.client.login(username="admin_payments", password="adminpass")

		payment = Payment.objects.create(
			student=self.student,
			course=self.course,
			amount=self.course.price,
			bank_account=self.bank,
			proof_receipt="private/payment-proofs/student/3/receipt.pdf",
			transaction_reference="TXN-FALLBACK",
			status=Payment.Status.PENDING,
		)

		# Mock storage to fail, forcing presigned URL fallback
		mock_private_storage = MagicMock()
		mock_private_storage.url.side_effect = Exception("storage url failed")
		mock_storages.__getitem__.return_value = mock_private_storage

		# Mock boto3.client() to return a mock client with proper bucket location detection
		mock_client = MagicMock()
		mock_client.get_bucket_location.return_value = {"LocationConstraint": "ap-south-1"}
		mock_client.generate_presigned_url.return_value = "https://signed.example.com/payment-receipt"
		mock_boto3_module.client.return_value = mock_client

		response = self.client.get(reverse("payments:admin_payments"))

		self.assertEqual(response.status_code, status.HTTP_200_OK)
		receipt = next(item for item in response.data if item["id"] == payment.id)
		self.assertEqual(receipt["proof_receipt_url"], "https://signed.example.com/payment-receipt")
		self.assertEqual(receipt["proof_receipt"], "https://signed.example.com/payment-receipt")

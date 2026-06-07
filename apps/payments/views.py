import os

from django.db import transaction
from django.core.files.storage import storages
from django.shortcuts import get_object_or_404
from django.utils.text import get_valid_filename
from django.utils import timezone
from rest_framework import permissions, status
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.enrollments.models import Enrollment
from .models import BankAccount, Payment
from .serializers import (
	BankAccountSerializer,
	OfflinePaymentSubmitSerializer,
	PaymentActionSerializer,
	PaymentSerializer,
)


class IsAdminPermission(permissions.BasePermission):
	def has_permission(self, request, view):
		user = request.user
		return bool(user and user.is_authenticated and (user.is_staff or getattr(user, "role", None) == "admin"))


class PublicBankAccountListView(APIView):
	permission_classes = [permissions.AllowAny]

	def get(self, request):
		accounts = BankAccount.objects.filter(is_active=True).order_by("-created_at")
		return Response(BankAccountSerializer(accounts, many=True).data, status=status.HTTP_200_OK)


class AdminBankAccountListCreateView(ListCreateAPIView):
	permission_classes = [IsAdminPermission]
	serializer_class = BankAccountSerializer
	queryset = BankAccount.objects.all().order_by("-created_at")


class AdminBankAccountDetailView(RetrieveUpdateDestroyAPIView):
	permission_classes = [IsAdminPermission]
	serializer_class = BankAccountSerializer
	queryset = BankAccount.objects.all()


class OfflinePaymentSubmitView(APIView):
	permission_classes = [permissions.IsAuthenticated]
	parser_classes = [MultiPartParser, FormParser, JSONParser]

	def post(self, request):
		serializer = OfflinePaymentSubmitSerializer(data=request.data, context={})
		serializer.is_valid(raise_exception=True)
		course = serializer.context["course"]
		bank_account = serializer.context["bank_account"]
		receipt_upload = serializer.validated_data.get("proof_receipt")
		receipt_key = ""
		if receipt_upload:
			safe_name = get_valid_filename(os.path.basename(receipt_upload.name))
			storage = storages["private"]
			path = f"payment-proofs/{request.user.id}/{course.id}/{safe_name}"
			saved = storage.save(path, receipt_upload)
			receipt_key = f"private/{saved}"

		# Already enrolled students should not create duplicate purchases.
		if Enrollment.objects.filter(student=request.user, course=course, is_active=True).exists():
			return Response({"detail": "You are already enrolled in this course."}, status=status.HTTP_400_BAD_REQUEST)

		existing_pending = Payment.objects.filter(
			student=request.user,
			course=course,
			status=Payment.Status.PENDING,
		).first()
		if existing_pending:
			return Response(
				{"detail": "You already submitted a pending payment for this course.", "payment": PaymentSerializer(existing_pending).data},
				status=status.HTTP_200_OK,
			)

		payment = Payment.objects.create(
			student=request.user,
			course=course,
			amount=course.price,
			bank_account=bank_account,
			proof_receipt=receipt_key,
			transaction_reference=serializer.validated_data.get("transaction_reference", ""),
			proof_note=serializer.validated_data.get("proof_note", ""),
			status=Payment.Status.PENDING,
		)
		return Response(PaymentSerializer(payment).data, status=status.HTTP_201_CREATED)


class AdminPaymentListView(APIView):
	permission_classes = [IsAdminPermission]

	def get(self, request):
		status_filter = request.query_params.get("status")
		queryset = Payment.objects.select_related("student", "course", "bank_account", "approved_by").order_by("-created_at")
		if status_filter:
			queryset = queryset.filter(status=status_filter)
		return Response(PaymentSerializer(queryset, many=True).data, status=status.HTTP_200_OK)


class AdminPaymentApproveView(APIView):
	permission_classes = [IsAdminPermission]

	@transaction.atomic
	def post(self, request, pk):
		payment = get_object_or_404(Payment, pk=pk)

		if payment.status == Payment.Status.APPROVED:
			enrollment, _ = Enrollment.objects.get_or_create(
				student=payment.student,
				course=payment.course,
				defaults={"is_active": True},
			)
			if not enrollment.is_active:
				enrollment.is_active = True
				enrollment.save(update_fields=["is_active"])
			return Response(
				{
					"detail": "Payment already approved.",
					"payment": PaymentSerializer(payment).data,
					"enrollment_id": enrollment.id,
				},
				status=status.HTTP_200_OK,
			)

		if payment.status == Payment.Status.REJECTED:
			return Response({"detail": "Rejected payments cannot be approved."}, status=status.HTTP_400_BAD_REQUEST)

		payment.status = Payment.Status.APPROVED
		payment.approved_by = request.user
		payment.approved_at = timezone.now()
		payment.rejection_reason = ""
		payment.save(update_fields=["status", "approved_by", "approved_at", "rejection_reason", "updated_at"])

		enrollment, _ = Enrollment.objects.get_or_create(
			student=payment.student,
			course=payment.course,
			defaults={"is_active": True},
		)
		if not enrollment.is_active:
			enrollment.is_active = True
			enrollment.save(update_fields=["is_active"])

		return Response(
			{
				"detail": "Payment approved and enrollment created.",
				"payment": PaymentSerializer(payment).data,
				"enrollment_id": enrollment.id,
			},
			status=status.HTTP_200_OK,
		)


class AdminPaymentRejectView(APIView):
	permission_classes = [IsAdminPermission]

	def post(self, request, pk):
		payment = get_object_or_404(Payment, pk=pk)
		serializer = PaymentActionSerializer(data=request.data)
		serializer.is_valid(raise_exception=True)

		if payment.status == Payment.Status.APPROVED:
			return Response({"detail": "Approved payments cannot be rejected."}, status=status.HTTP_400_BAD_REQUEST)

		payment.status = Payment.Status.REJECTED
		payment.approved_by = request.user
		payment.approved_at = timezone.now()
		payment.rejection_reason = serializer.validated_data.get("rejection_reason", "")
		payment.save(update_fields=["status", "approved_by", "approved_at", "rejection_reason", "updated_at"])

		return Response({"detail": "Payment rejected.", "payment": PaymentSerializer(payment).data}, status=status.HTTP_200_OK)


class MyPaymentsView(APIView):
	permission_classes = [permissions.IsAuthenticated]

	def get(self, request):
		queryset = Payment.objects.filter(student=request.user).order_by("-created_at")
		return Response(PaymentSerializer(queryset, many=True).data, status=status.HTTP_200_OK)

from django.shortcuts import get_object_or_404
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Enrollment
from .serializers import AdminEnrollmentCreateSerializer, EnrollmentSerializer


class IsAdminPermission(permissions.BasePermission):
	def has_permission(self, request, view):
		user = request.user
		return bool(user and user.is_authenticated and (user.is_staff or getattr(user, "role", None) == "admin"))


class MyEnrollmentListView(APIView):
	permission_classes = [permissions.IsAuthenticated]

	def get(self, request):
		queryset = Enrollment.objects.filter(student=request.user, is_active=True).select_related("course", "student")
		return Response(EnrollmentSerializer(queryset, many=True).data, status=status.HTTP_200_OK)


class AdminEnrollmentListCreateView(APIView):
	permission_classes = [IsAdminPermission]

	def get(self, request):
		queryset = Enrollment.objects.select_related("course", "student").order_by("-created_at")
		student_id = request.query_params.get("student_id")
		course_id = request.query_params.get("course_id")
		is_active = request.query_params.get("is_active")

		if student_id:
			queryset = queryset.filter(student_id=student_id)
		if course_id:
			queryset = queryset.filter(course_id=course_id)
		if is_active is not None:
			parsed = str(is_active).lower() in ("1", "true", "yes")
			queryset = queryset.filter(is_active=parsed)

		return Response(EnrollmentSerializer(queryset, many=True).data, status=status.HTTP_200_OK)

	def post(self, request):
		serializer = AdminEnrollmentCreateSerializer(data=request.data, context={})
		serializer.is_valid(raise_exception=True)

		student = serializer.context["student"]
		course = serializer.context["course"]

		enrollment, created = Enrollment.objects.get_or_create(
			student=student,
			course=course,
			defaults={"is_active": True},
		)
		if not created and not enrollment.is_active:
			enrollment.is_active = True
			enrollment.save(update_fields=["is_active"])

		message = "Enrollment created." if created else "Enrollment already existed; activated."
		return Response(
			{"detail": message, "enrollment": EnrollmentSerializer(enrollment).data},
			status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
		)


class AdminEnrollmentActivateView(APIView):
	permission_classes = [IsAdminPermission]

	def post(self, request, pk):
		enrollment = get_object_or_404(Enrollment, pk=pk)
		if not enrollment.is_active:
			enrollment.is_active = True
			enrollment.save(update_fields=["is_active"])
		return Response({"detail": "Enrollment activated."}, status=status.HTTP_200_OK)


class AdminEnrollmentDeactivateView(APIView):
	permission_classes = [IsAdminPermission]

	def post(self, request, pk):
		enrollment = get_object_or_404(Enrollment, pk=pk)
		if enrollment.is_active:
			enrollment.is_active = False
			enrollment.save(update_fields=["is_active"])
		return Response({"detail": "Enrollment deactivated."}, status=status.HTTP_200_OK)

import os

import boto3
from django.conf import settings
from django.core.files.storage import storages
from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions, status
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.enrollments.models import Enrollment
from .models import Course, Lesson
from .serializers import (
	AdminCourseSerializer,
	AdminLessonSerializer,
	CourseDetailSerializer,
	CourseListSerializer,
	CourseThumbnailUploadSerializer,
	LessonSerializer,
)


class IsCourseAdminPermission(permissions.BasePermission):
	def has_permission(self, request, view):
		user = request.user
		return bool(user and user.is_authenticated and (user.is_staff or getattr(user, "role", None) == "admin"))


def _is_course_admin(user):
	return bool(user and user.is_authenticated and (user.is_staff or getattr(user, "role", None) == "admin"))


def _normalize_public_storage_key(s3_key: str) -> str:
	key = s3_key.lstrip("/")
	if key.startswith("public/"):
		return key[len("public/") :]
	return key


def _public_url_for_key(s3_key: str):
	if not s3_key:
		return None
	if isinstance(s3_key, str) and s3_key.startswith(("http://", "https://")):
		return s3_key
	try:
		return storages["public"].url(_normalize_public_storage_key(s3_key))
	except Exception:
		key = _normalize_public_storage_key(s3_key)
		custom_domain = getattr(settings, "AWS_S3_CUSTOM_DOMAIN", None)
		if custom_domain:
			domain = custom_domain.rstrip("/")
			if domain.startswith(("http://", "https://")):
				return f"{domain}/public/{key}"
			return f"https://{domain}/public/{key}"

		bucket = getattr(settings, "AWS_STORAGE_BUCKET_NAME", None)
		if not bucket:
			return None
		return f"https://{bucket}.s3.amazonaws.com/public/{key}"


class CourseCatalogView(generics.ListAPIView):
	permission_classes = [permissions.AllowAny]
	serializer_class = CourseListSerializer

	def get_queryset(self):
		queryset = Course.objects.all() if _is_course_admin(self.request.user) else Course.objects.filter(status=Course.Status.PUBLISHED)
		q = self.request.query_params.get("q")
		category = self.request.query_params.get("category")

		if q:
			queryset = queryset.filter(title__icontains=q)
		if category:
			queryset = queryset.filter(category__icontains=category)
		return queryset.order_by("-is_featured", "-created_at")


class CourseDetailView(generics.RetrieveAPIView):
	permission_classes = [permissions.AllowAny]
	serializer_class = CourseDetailSerializer
	lookup_field = "slug"

	def get_queryset(self):
		queryset = Course.objects.all() if _is_course_admin(self.request.user) else Course.objects.filter(status=Course.Status.PUBLISHED)
		return queryset.prefetch_related("lessons")


class CourseLessonsView(APIView):
	permission_classes = [permissions.AllowAny]

	def get(self, request, slug):
		course_queryset = Course.objects.all() if _is_course_admin(request.user) else Course.objects.filter(status=Course.Status.PUBLISHED)
		course = get_object_or_404(course_queryset, slug=slug)
		lessons = course.lessons.all().order_by("order", "id")
		serializer = LessonSerializer(lessons, many=True, context={"request": request})
		return Response(serializer.data, status=status.HTTP_200_OK)


class LessonAccessView(APIView):
	permission_classes = [permissions.AllowAny]

	def get(self, request, pk):
		lesson = get_object_or_404(Lesson.objects.select_related("course"), pk=pk)
		if lesson.course.status != Course.Status.PUBLISHED and not _is_course_admin(request.user):
			return Response({"detail": "Lesson not available."}, status=status.HTTP_404_NOT_FOUND)

		# Preview lessons are free and served via public URL.
		if lesson.is_preview:
			url = _public_url_for_key(lesson.s3_key)
			if not url:
				return Response({"detail": "Preview URL unavailable."}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
			return Response({"url": url, "preview": True}, status=status.HTTP_200_OK)

		# Paid lessons require authentication + active enrollment.
		if not request.user.is_authenticated:
			return Response({"detail": "Authentication required."}, status=status.HTTP_401_UNAUTHORIZED)

		enrolled = Enrollment.objects.filter(student=request.user, course=lesson.course, is_active=True).exists()
		if not enrolled:
			return Response({"detail": "Purchase course first."}, status=status.HTTP_403_FORBIDDEN)

		bucket = getattr(settings, "AWS_STORAGE_BUCKET_NAME", None)
		if not bucket:
			return Response({"detail": "Storage is not configured."}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

		expires = int(getattr(settings, "COURSE_PRESIGNED_EXPIRES", 3600))
		
		# Detect bucket region - start with us-east-1 as default, then probe for actual region
		bucket_region = "us-east-1"
		try:
			# Use us-east-1 explicitly to probe (neutral region that can access any bucket)
			probe_client = boto3.client(
				"s3",
				aws_access_key_id=getattr(settings, "AWS_ACCESS_KEY_ID", None),
				aws_secret_access_key=getattr(settings, "AWS_SECRET_ACCESS_KEY", None),
				region_name="us-east-1",
			)
			loc = probe_client.get_bucket_location(Bucket=bucket)
			detected_region = loc.get("LocationConstraint")
			# LocationConstraint is None for us-east-1 buckets, keep default in that case
			if detected_region:
				bucket_region = detected_region
		except Exception:
			# If probe fails, try settings value, otherwise keep us-east-1 default
			settings_region = getattr(settings, "AWS_S3_REGION_NAME", None)
			if settings_region:
				bucket_region = settings_region
		
		# Create a client bound to the detected bucket region for presigned URL generation
		s3 = boto3.client(
			"s3",
			aws_access_key_id=getattr(settings, "AWS_ACCESS_KEY_ID", None),
			aws_secret_access_key=getattr(settings, "AWS_SECRET_ACCESS_KEY", None),
			region_name=bucket_region,
		)
		url = s3.generate_presigned_url(
			"get_object",
			Params={"Bucket": bucket, "Key": lesson.s3_key.lstrip("/")},
			ExpiresIn=expires,
		)
		return Response({"url": url, "preview": False, "expires_in": expires}, status=status.HTTP_200_OK)


class AdminCourseListCreateView(generics.ListCreateAPIView):
	permission_classes = [IsCourseAdminPermission]
	serializer_class = AdminCourseSerializer
	queryset = Course.objects.all().order_by("-created_at")

	def perform_create(self, serializer):
		serializer.save(created_by=self.request.user)


class AdminCourseDetailView(generics.RetrieveUpdateDestroyAPIView):
	permission_classes = [IsCourseAdminPermission]
	serializer_class = AdminCourseSerializer
	queryset = Course.objects.all()


class AdminCoursePublishView(APIView):
	permission_classes = [IsCourseAdminPermission]

	def post(self, request, pk):
		course = get_object_or_404(Course, pk=pk)
		course.status = Course.Status.PUBLISHED
		course.save(update_fields=["status", "updated_at"])
		return Response({"detail": "Course published.", "status": course.status}, status=status.HTTP_200_OK)


class AdminCourseThumbnailUploadView(APIView):
	permission_classes = [IsCourseAdminPermission]

	def post(self, request, pk):
		course = get_object_or_404(Course, pk=pk)
		serializer = CourseThumbnailUploadSerializer(data=request.data)
		serializer.is_valid(raise_exception=True)

		upload = serializer.validated_data["file"]
		safe_name = os.path.basename(upload.name)
		path = f"thumbnails/{course.slug}/{safe_name}"

		storage = storages["public"]
		saved = storage.save(path, upload)
		course.thumbnail = saved
		course.save(update_fields=["thumbnail", "updated_at"])

		url = _public_url_for_key(saved)
		return Response({"thumbnail": url or "", "thumbnail_key": saved, "url": url or ""}, status=status.HTTP_201_CREATED)


class AdminLessonCreateView(generics.CreateAPIView):
	permission_classes = [IsCourseAdminPermission]
	serializer_class = AdminLessonSerializer
	parser_classes = [MultiPartParser, FormParser, JSONParser]


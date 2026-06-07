from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.courses.models import Course, Lesson
from apps.enrollments.models import Enrollment
from .models import LessonProgress
from .serializers import LessonProgressSerializer


class LessonCompleteView(APIView):
	permission_classes = [permissions.IsAuthenticated]

	def post(self, request, pk):
		lesson = get_object_or_404(Lesson.objects.select_related("course"), pk=pk)
		course = lesson.course

		if course.status != Course.Status.PUBLISHED:
			return Response({"detail": "Lesson not available."}, status=status.HTTP_404_NOT_FOUND)

		if not lesson.is_preview:
			enrolled = Enrollment.objects.filter(student=request.user, course=course, is_active=True).exists()
			if not enrolled:
				return Response({"detail": "Purchase course first."}, status=status.HTTP_403_FORBIDDEN)

		progress, _ = LessonProgress.objects.get_or_create(student=request.user, lesson=lesson)
		progress.is_completed = True
		progress.completed_at = timezone.now()
		progress.save(update_fields=["is_completed", "completed_at", "updated_at"])

		return Response(LessonProgressSerializer(progress).data, status=status.HTTP_200_OK)


class CourseProgressView(APIView):
	permission_classes = [permissions.IsAuthenticated]

	def get(self, request, slug):
		course = get_object_or_404(Course, slug=slug, status=Course.Status.PUBLISHED)

		total_lessons = course.lessons.count()
		completed_lessons = LessonProgress.objects.filter(
			student=request.user,
			lesson__course=course,
			is_completed=True,
		).count()
		percent = 0.0
		if total_lessons > 0:
			percent = round((completed_lessons / total_lessons) * 100, 2)

		completed_items = LessonProgress.objects.filter(
			student=request.user,
			lesson__course=course,
			is_completed=True,
		).select_related("lesson")

		return Response(
			{
				"course_id": course.id,
				"course_slug": course.slug,
				"total_lessons": total_lessons,
				"completed_lessons": completed_lessons,
				"completion_percent": percent,
				"completed": LessonProgressSerializer(completed_items, many=True).data,
			},
			status=status.HTTP_200_OK,
		)

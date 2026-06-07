from django.contrib.auth import get_user_model
from rest_framework import serializers

from apps.courses.models import Course
from .models import Enrollment

User = get_user_model()


class EnrollmentSerializer(serializers.ModelSerializer):
    student_username = serializers.CharField(source="student.username", read_only=True)
    course_title = serializers.CharField(source="course.title", read_only=True)
    course_slug = serializers.CharField(source="course.slug", read_only=True)

    class Meta:
        model = Enrollment
        fields = (
            "id",
            "student",
            "student_username",
            "course",
            "course_title",
            "course_slug",
            "is_active",
            "created_at",
        )


class AdminEnrollmentCreateSerializer(serializers.Serializer):
    student_id = serializers.UUIDField()
    course_id = serializers.IntegerField()

    def validate_student_id(self, value):
        try:
            student = User.objects.get(pk=value)
        except User.DoesNotExist as exc:
            raise serializers.ValidationError("Student not found.") from exc
        self.context["student"] = student
        return value

    def validate_course_id(self, value):
        try:
            course = Course.objects.get(pk=value)
        except Course.DoesNotExist as exc:
            raise serializers.ValidationError("Course not found.") from exc
        self.context["course"] = course
        return value

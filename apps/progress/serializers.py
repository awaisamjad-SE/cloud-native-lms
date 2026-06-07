from rest_framework import serializers

from .models import LessonProgress


class LessonProgressSerializer(serializers.ModelSerializer):
    lesson_title = serializers.CharField(source="lesson.title", read_only=True)
    course_id = serializers.IntegerField(source="lesson.course_id", read_only=True)

    class Meta:
        model = LessonProgress
        fields = (
            "id",
            "lesson",
            "lesson_title",
            "course_id",
            "is_completed",
            "completed_at",
            "updated_at",
        )
        read_only_fields = ("id", "completed_at", "updated_at", "lesson_title", "course_id")

from django.contrib import admin
from .models import Course, Lesson


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
	list_display = ("id", "title", "status", "price", "category", "is_featured", "created_at")
	list_filter = ("status", "category", "is_featured")
	search_fields = ("title", "slug", "category")
	prepopulated_fields = {"slug": ("title",)}


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
	list_display = ("id", "course", "title", "lesson_type", "is_preview", "order", "duration")
	list_filter = ("lesson_type", "is_preview")
	search_fields = ("title", "course__title", "s3_key")

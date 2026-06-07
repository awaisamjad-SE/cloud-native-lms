from django.contrib import admin

from .models import Enrollment


@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ("id", "student", "course", "is_active", "created_at")
    list_filter = ("is_active", "created_at")
    search_fields = ("student__username", "student__email", "course__title", "course__slug")

from django.urls import path

from .views import (
    AdminCourseDetailView,
    AdminCourseListCreateView,
    AdminCoursePublishView,
    AdminCourseThumbnailUploadView,
    AdminLessonCreateView,
    CourseCatalogView,
    CourseDetailView,
    CourseLessonsView,
    LessonAccessView,
)

app_name = "courses"

urlpatterns = [
    # Public + student endpoints
    path("courses/", CourseCatalogView.as_view(), name="course_catalog"),
    path("courses/<slug:slug>/", CourseDetailView.as_view(), name="course_detail"),
    path("courses/<slug:slug>/lessons/", CourseLessonsView.as_view(), name="course_lessons"),
    path("lessons/<int:pk>/access/", LessonAccessView.as_view(), name="lesson_access"),

    # Admin endpoints
    path("admin/courses/", AdminCourseListCreateView.as_view(), name="admin_course_list_create"),
    path("admin/courses/<int:pk>/", AdminCourseDetailView.as_view(), name="admin_course_detail"),
    path("admin/courses/<int:pk>/publish/", AdminCoursePublishView.as_view(), name="admin_course_publish"),
    path("admin/courses/<int:pk>/thumbnail/", AdminCourseThumbnailUploadView.as_view(), name="admin_course_thumbnail"),
    path("admin/lessons/", AdminLessonCreateView.as_view(), name="admin_lesson_create"),
]

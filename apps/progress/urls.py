from django.urls import path

from .views import CourseProgressView, LessonCompleteView

app_name = "progress"

urlpatterns = [
    path("lessons/<int:pk>/complete/", LessonCompleteView.as_view(), name="lesson_complete"),
    path("courses/<slug:slug>/progress/", CourseProgressView.as_view(), name="course_progress"),
]

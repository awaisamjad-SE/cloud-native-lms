from django.urls import path

from .views import (
    AdminEnrollmentActivateView,
    AdminEnrollmentDeactivateView,
    AdminEnrollmentListCreateView,
    MyEnrollmentListView,
)

app_name = "enrollments"

urlpatterns = [
    path("enrollments/my/", MyEnrollmentListView.as_view(), name="my_enrollments"),
    path("admin/enrollments/", AdminEnrollmentListCreateView.as_view(), name="admin_enrollments"),
    path("admin/enrollments/<int:pk>/activate/", AdminEnrollmentActivateView.as_view(), name="admin_enrollment_activate"),
    path("admin/enrollments/<int:pk>/deactivate/", AdminEnrollmentDeactivateView.as_view(), name="admin_enrollment_deactivate"),
]

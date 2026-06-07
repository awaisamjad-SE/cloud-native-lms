from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import CustomTokenObtainPairView, RegisterView, ProfileView, ChangePasswordView
from .views import ProfileImageUploadView, PresignedProfileUploadView
from .admin_views import (
    AdminUserListView,
    AdminUserDetailView,
    AdminUserActivateView,
    AdminUserDeactivateView,
)

app_name = 'accounts'

urlpatterns = [
    # Public auth endpoints
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # Profile
    path('profile/', ProfileView.as_view(), name='profile'),
    path('profile/upload-image/', ProfileImageUploadView.as_view(), name='profile_upload_image'),
    path('profile/upload-image/presigned/', PresignedProfileUploadView.as_view(), name='profile_upload_image_presigned'),
    path('change-password/', ChangePasswordView.as_view(), name='change_password'),

    # Admin user management
    path('admin/users/', AdminUserListView.as_view(), name='admin_user_list'),
    path('admin/users/<uuid:pk>/', AdminUserDetailView.as_view(), name='admin_user_detail'),
    path('admin/users/<uuid:pk>/activate/', AdminUserActivateView.as_view(), name='admin_user_activate'),
    path('admin/users/<uuid:pk>/deactivate/', AdminUserDeactivateView.as_view(), name='admin_user_deactivate'),
]

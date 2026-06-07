from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth import get_user_model
from .serializers_admin import UserListSerializer, UserDetailSerializer

User = get_user_model()


class IsAdminPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and (request.user.is_staff or request.user.role == 'admin'))


class AdminUserListView(generics.ListAPIView):
    queryset = User.objects.all().order_by('-date_joined')
    serializer_class = UserListSerializer
    permission_classes = [IsAdminPermission]


class AdminUserDetailView(generics.RetrieveAPIView):
    queryset = User.objects.all()
    serializer_class = UserDetailSerializer
    permission_classes = [IsAdminPermission]


class AdminUserActivateView(APIView):
    permission_classes = [IsAdminPermission]

    def post(self, request, pk):
        try:
            user = User.objects.get(pk=pk)
        except User.DoesNotExist:
            return Response({'detail': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)
        user.is_active = True
        user.save()
        return Response({'detail': 'User activated.'})


class AdminUserDeactivateView(APIView):
    permission_classes = [IsAdminPermission]

    def post(self, request, pk):
        try:
            user = User.objects.get(pk=pk)
        except User.DoesNotExist:
            return Response({'detail': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)
        user.is_active = False
        user.save()
        return Response({'detail': 'User deactivated.'})

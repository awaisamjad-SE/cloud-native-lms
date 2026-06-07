from rest_framework import serializers
from django.contrib.auth import get_user_model

User = get_user_model()


class UserListSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name', 'role', 'is_active', 'is_staff')


class UserDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name', 'role', 'is_active', 'is_staff', 'date_joined')

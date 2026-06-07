from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.conf import settings
from django.core.files.storage import storages
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from .models import UserProfile

User = get_user_model()


def _public_url_from_key(s3_key: str) -> str:
    if not s3_key:
        return ""
    if isinstance(s3_key, str) and s3_key.startswith(("http://", "https://")):
        return s3_key

    key = str(s3_key).lstrip("/")
    if key.startswith("public/"):
        key = key[len("public/") :]

    try:
        return storages["public"].url(key)
    except Exception:
        custom_domain = getattr(settings, "AWS_S3_CUSTOM_DOMAIN", None)
        if custom_domain:
            domain = custom_domain.rstrip("/")
            if domain.startswith(("http://", "https://")):
                return f"{domain}/public/{key}"
            return f"https://{domain}/public/{key}"

        bucket = getattr(settings, "AWS_STORAGE_BUCKET_NAME", None)
        if not bucket:
            return ""
        return f"https://{bucket}.s3.amazonaws.com/public/{key}"


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ('username', 'email', 'password', 'first_name', 'last_name')

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user


class ProfileSerializer(serializers.ModelSerializer):
    profile_image = serializers.SerializerMethodField()
    phone_number = serializers.CharField(source='profile.phone_number', allow_blank=True, read_only=True)
    bio = serializers.CharField(source='profile.bio', allow_blank=True, read_only=True)

    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'role', 'profile_image', 'phone_number', 'bio')

    def get_profile_image(self, obj):
        profile = getattr(obj, "profile", None)
        if not profile:
            return ""
        return _public_url_from_key(profile.profile_image)


class UpdateProfileSerializer(serializers.ModelSerializer):
    phone_number = serializers.CharField(write_only=True, required=False, allow_blank=True)
    bio = serializers.CharField(write_only=True, required=False, allow_blank=True)
    profile_image = serializers.CharField(write_only=True, required=False, allow_blank=True)

    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'phone_number', 'bio', 'profile_image')

    def update(self, instance, validated_data):
        profile_data = {}
        for key in ('phone_number', 'bio', 'profile_image'):
            if key in validated_data:
                profile_data[key] = validated_data.pop(key)

        instance = super().update(instance, validated_data)

        profile, _ = instance.profile.__class__.objects.get_or_create(user=instance)
        for k, v in profile_data.items():
            setattr(profile, k, v)
        profile.save()
        return instance


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True)


class ProfileImageUploadSerializer(serializers.Serializer):
    file = serializers.ImageField()

    def validate_file(self, value):
        # optional: limit file size to 5MB
        max_size = 5 * 1024 * 1024
        if value.size > max_size:
            raise serializers.ValidationError("Image too large. Max size is 5 MB.")
        return value


class LoginUserSerializer(serializers.ModelSerializer):
    profile_image = serializers.SerializerMethodField()
    phone_number = serializers.SerializerMethodField()
    bio = serializers.SerializerMethodField()
    staff_member = serializers.BooleanField(source="is_staff", read_only=True)

    class Meta:
        model = User
        fields = (
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "role",
            "is_email_verified",
            "profile_image",
            "phone_number",
            "bio",
            "staff_member"
        )

    def _get_profile(self, obj):
        profile = getattr(obj, "profile", None)
        if profile is not None:
            return profile
        return UserProfile.objects.filter(user=obj).first()

    def get_profile_image(self, obj):
        profile = self._get_profile(obj)
        if not profile:
            return ""
        return _public_url_from_key(profile.profile_image)

    def get_phone_number(self, obj):
        profile = self._get_profile(obj)
        return profile.phone_number if profile else ""

    def get_bio(self, obj):
        profile = self._get_profile(obj)
        return profile.bio if profile else ""


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)
        data["user"] = LoginUserSerializer(self.user).data
        return data
import os

from django.conf import settings
from django.core.files.storage import storages
from django.utils.text import get_valid_filename
from rest_framework import serializers

from apps.enrollments.models import Enrollment
from .models import Course, Lesson


def _public_url_from_key(s3_key: str):
    if not s3_key:
        return None
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
            return None
        return f"https://{bucket}.s3.amazonaws.com/public/{key}"


class LessonSerializer(serializers.ModelSerializer):
    locked = serializers.SerializerMethodField()

    class Meta:
        model = Lesson
        fields = (
            "id",
            "title",
            "description",
            "lesson_type",
            "is_preview",
            "order",
            "duration",
            "locked",
        )

    def get_locked(self, obj):
        if obj.is_preview:
            return False
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return True
        return not Enrollment.objects.filter(student=request.user, course=obj.course, is_active=True).exists()


class CourseListSerializer(serializers.ModelSerializer):
    thumbnail_url = serializers.SerializerMethodField()

    class Meta:
        model = Course
        fields = ("id", "title", "slug", "price", "category", "thumbnail_url", "is_featured")

    def get_thumbnail_url(self, obj):
        return _public_url_from_key(obj.thumbnail)


class CourseDetailSerializer(serializers.ModelSerializer):
    lessons = LessonSerializer(many=True, read_only=True)
    thumbnail_url = serializers.SerializerMethodField()

    class Meta:
        model = Course
        fields = (
            "id",
            "title",
            "slug",
            "description",
            "price",
            "category",
            "status",
            "is_featured",
            "thumbnail_url",
            "lessons",
        )

    def get_thumbnail_url(self, obj):
        return _public_url_from_key(obj.thumbnail)


class AdminCourseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Course
        fields = (
            "id",
            "title",
            "slug",
            "description",
            "thumbnail",
            "price",
            "category",
            "status",
            "is_featured",
            "created_by",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("created_by", "created_at", "updated_at")

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data["thumbnail_key"] = instance.thumbnail or ""
        data["thumbnail"] = _public_url_from_key(instance.thumbnail) or ""
        return data


class AdminLessonSerializer(serializers.ModelSerializer):
    key = serializers.CharField(source="s3_key", read_only=True)
    url = serializers.SerializerMethodField()
    file = serializers.FileField(write_only=True, required=False)
    MAX_UPLOAD_SIZE = 20 * 1024 * 1024

    class Meta:
        model = Lesson
        fields = (
            "id",
            "course",
            "title",
            "description",
            "lesson_type",
            "s3_key",
            "key",
            "url",
            "is_preview",
            "order",
            "duration",
            "file",
            "created_at",
        )
        read_only_fields = ("created_at",)
        extra_kwargs = {"s3_key": {"required": False}}

    def validate_s3_key(self, value):
        cleaned = value.strip().lstrip("/")
        if not cleaned:
            raise serializers.ValidationError("s3_key is required.")
        return cleaned

    def validate_file(self, value):
        if value.size > self.MAX_UPLOAD_SIZE:
            raise serializers.ValidationError("File too large. Max size is 20 MB.")
        return value

    def validate(self, attrs):
        upload = attrs.get("file")
        is_preview = attrs.get("is_preview", getattr(self.instance, "is_preview", False))
        s3_key = attrs.get("s3_key", getattr(self.instance, "s3_key", ""))

        if not upload and not s3_key:
            raise serializers.ValidationError({"file": "Provide a file or s3_key."})

        if not upload and is_preview and not s3_key.startswith("public/"):
            raise serializers.ValidationError({"s3_key": "Preview lessons must use a public/ S3 key."})
        if not upload and not is_preview and not s3_key.startswith("private/"):
            raise serializers.ValidationError({"s3_key": "Paid lessons must use a private/ S3 key."})
        return attrs

    def create(self, validated_data):
        upload = validated_data.pop("file", None)
        is_preview = validated_data.get("is_preview", False)

        if upload:
            safe_name = get_valid_filename(os.path.basename(upload.name))
            storage_name = "public" if is_preview else "private"
            storage = storages[storage_name]
            lesson_type = validated_data["lesson_type"]
            folder = "previews" if is_preview else f"{lesson_type}s"
            saved = storage.save(f"{folder}/{safe_name}", upload)
            validated_data["s3_key"] = f"{storage_name}/{saved}"

        return super().create(validated_data)

    def get_url(self, obj):
        s3_key = getattr(obj, "s3_key", "") or ""
        if not s3_key:
            return None

        storage_name = "public" if s3_key.startswith("public/") else "private"
        storage = storages[storage_name]
        storage_key = s3_key[len(f"{storage_name}/") :] if s3_key.startswith(f"{storage_name}/") else s3_key

        try:
            return storage.url(storage_key)
        except Exception:
            return None


class CourseThumbnailUploadSerializer(serializers.Serializer):
    file = serializers.ImageField()

    def validate_file(self, value):
        max_size = 5 * 1024 * 1024
        if value.size > max_size:
            raise serializers.ValidationError("Image too large. Max size is 5 MB.")
        filename = os.path.basename(value.name)
        if not filename:
            raise serializers.ValidationError("Invalid filename.")
        return value

from rest_framework import generics, permissions, status
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView
from django.core.files.storage import storages
import boto3
from django.conf import settings
from django.utils.text import get_valid_filename
import os
from .models import UserProfile

from .serializers import (
    CustomTokenObtainPairSerializer,
    RegisterSerializer,
    ProfileSerializer,
    UpdateProfileSerializer,
    ChangePasswordSerializer,
)

User = get_user_model()


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer


class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        # Return minimal message per SRS plus user id
        return Response({'message': 'Registration successful', 'id': str(user.id)}, status=status.HTTP_201_CREATED)


class LoginView(generics.GenericAPIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        # Delegate to SimpleJWT TokenObtainPairView in urls; kept for completeness
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)


class ProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = ProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user

    def patch(self, request, *args, **kwargs):
        self.serializer_class = UpdateProfileSerializer
        return self.partial_update(request, *args, **kwargs)


class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = request.user
        if not user.check_password(serializer.validated_data['old_password']):
            return Response({'old_password': ['Wrong password.']}, status=status.HTTP_400_BAD_REQUEST)
        user.set_password(serializer.validated_data['new_password'])
        user.save()
        return Response({'detail': 'Password updated.'}, status=status.HTTP_200_OK)


class ProfileImageUploadView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = None
        from .serializers import ProfileImageUploadSerializer

        serializer = ProfileImageUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        upload = serializer.validated_data['file']
        user = request.user

        # build a safe filename and path; store under profiles/{user_id}/
        # NOTE: do NOT prefix with "public/" here because the `public`
        # storage backend already uses `location = 'public'` and will
        # prepend that when saving. Passing "public/..." caused a
        # duplicated "public/public/..." key in S3.
        filename = get_valid_filename(os.path.basename(upload.name))
        prefix = f"profiles/{user.id}"
        # Use forward slash to ensure S3 key style path on all platforms
        path = f"{prefix}/{filename}"

        public_storage = storages["public"]

        # public storage saves to the `public/` prefix in S3
        saved_name = public_storage.save(path, upload)

        # ensure profile exists without accessing user.profile which may raise
        profile, _ = UserProfile.objects.get_or_create(user=user)
        profile.profile_image = saved_name
        profile.save()

        # attempt to get a URL from storage; some setups may need presigned URLs separately
        try:
            url = public_storage.url(saved_name)
        except Exception:
            custom_domain = getattr(settings, "AWS_S3_CUSTOM_DOMAIN", None)
            if custom_domain:
                domain = custom_domain.rstrip("/")
                if domain.startswith(("http://", "https://")):
                    url = f"{domain}/public/{saved_name}"
                else:
                    url = f"https://{domain}/public/{saved_name}"
            else:
                bucket = getattr(settings, "AWS_STORAGE_BUCKET_NAME", None)
                url = f"https://{bucket}.s3.amazonaws.com/public/{saved_name}" if bucket else None

        return Response(
            {
                "profile_image": url,
                "profile_image_key": saved_name,
                "url": url,
                "key": saved_name,
            },
            status=status.HTTP_201_CREATED,
        )


class PresignedProfileUploadView(APIView):
    """Return S3 presigned POST data so the client can upload directly.

    This avoids proxying files through Django and avoids ACL errors when
    the bucket has "Object Ownership: Bucket owner enforced" (which
    disallows ACLs). Note: when uploading directly, the S3 key must
    include the `public/` prefix because storage `location='public'`
    is only applied by the storage backend on server-side saves.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        filename = request.data.get("filename")
        if not filename:
            return Response({"detail": "filename required"}, status=status.HTTP_400_BAD_REQUEST)

        user = request.user
        safe_name = get_valid_filename(os.path.basename(filename))
        key = f"public/profiles/{user.id}/{safe_name}"

        # Use boto3 client; credentials/region come from environment or settings
        s3 = boto3.client(
            "s3",
            aws_access_key_id=getattr(settings, "AWS_ACCESS_KEY_ID", None),
            aws_secret_access_key=getattr(settings, "AWS_SECRET_ACCESS_KEY", None),
            region_name=getattr(settings, "AWS_S3_REGION_NAME", None),
        )

        # If your bucket blocks ACLs (AccessControlListNotSupported), do NOT
        # include an 'acl' field here; instead rely on a bucket policy to make
        # objects public or return only a presigned PUT URL for authenticated access.
        include_acl = False

        fields = {}
        conditions = [["starts-with", "$key", f"public/profiles/{user.id}/"]]

        if include_acl:
            fields["acl"] = "public-read"
            conditions.append({"acl": "public-read"})

        presigned = s3.generate_presigned_post(
            Bucket=settings.AWS_STORAGE_BUCKET_NAME,
            Key=key,
            Fields=fields,
            Conditions=conditions,
            ExpiresIn=3600,
        )

        return Response({"key": key, "data": presigned})


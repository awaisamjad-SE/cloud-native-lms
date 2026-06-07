import os

import boto3
from django.conf import settings
from django.core.files.storage import storages
from django.utils.text import get_valid_filename
from rest_framework import serializers

from apps.courses.models import Course
from .models import BankAccount, Payment


class OfflinePaymentSubmitSerializer(serializers.Serializer):
    course_id = serializers.IntegerField()
    bank_account_id = serializers.IntegerField()
    transaction_reference = serializers.CharField(required=False, allow_blank=True, default="")
    proof_note = serializers.CharField(required=False, allow_blank=True, default="")
    proof_receipt = serializers.FileField(required=False, allow_null=True)

    def validate_course_id(self, value):
        try:
            course = Course.objects.get(pk=value)
        except Course.DoesNotExist as exc:
            raise serializers.ValidationError("Course not found.") from exc
        if course.status != Course.Status.PUBLISHED:
            raise serializers.ValidationError("Only published courses can be purchased.")
        self.context["course"] = course
        return value

    def validate_bank_account_id(self, value):
        try:
            bank_account = BankAccount.objects.get(pk=value, is_active=True)
        except BankAccount.DoesNotExist as exc:
            raise serializers.ValidationError("Active bank account not found.") from exc
        self.context["bank_account"] = bank_account
        return value

    def save_receipt_to_storage(self, upload, student_id, course_id):
        safe_name = get_valid_filename(os.path.basename(upload.name))
        storage = storages["private"]
        path = f"payment-proofs/{student_id}/{course_id}/{safe_name}"
        saved = storage.save(path, upload)
        return f"private/{saved}"


def get_private_url_from_key(file_key: str):
    if not file_key:
        return None
    if isinstance(file_key, str) and file_key.startswith(("http://", "https://")):
        return file_key

    key = str(file_key).lstrip("/")
    if key.startswith("private/"):
        key = key[len("private/") :]

    bucket = getattr(settings, "AWS_STORAGE_BUCKET_NAME", None)
    if not bucket:
        return None

    # Detect bucket region - start with us-east-1 as a neutral probe region.
    bucket_region = "us-east-1"
    try:
        probe_client = boto3.client(
            "s3",
            aws_access_key_id=getattr(settings, "AWS_ACCESS_KEY_ID", None),
            aws_secret_access_key=getattr(settings, "AWS_SECRET_ACCESS_KEY", None),
            region_name="us-east-1",
        )
        loc = probe_client.get_bucket_location(Bucket=bucket)
        detected_region = loc.get("LocationConstraint")
        if detected_region:
            bucket_region = detected_region
    except Exception:
        settings_region = getattr(settings, "AWS_S3_REGION_NAME", None)
        if settings_region:
            bucket_region = settings_region

    if not bucket_region:
        bucket_region = "us-east-1"

    try:
        client = boto3.client(
            "s3",
            aws_access_key_id=getattr(settings, "AWS_ACCESS_KEY_ID", None),
            aws_secret_access_key=getattr(settings, "AWS_SECRET_ACCESS_KEY", None),
            region_name=bucket_region,
        )
        return client.generate_presigned_url(
            "get_object",
            Params={"Bucket": bucket, "Key": f"private/{key}"},
            ExpiresIn=int(getattr(settings, "PRIVATE_URL_EXPIRES", 3600)),
        )
    except Exception:
        try:
            storage = storages["private"]
            return storage.url(key)
        except Exception:
            custom_domain = getattr(settings, "AWS_S3_CUSTOM_DOMAIN", None)
            if custom_domain:
                domain = custom_domain.rstrip("/")
                if domain.startswith(("http://", "https://")):
                    return f"{domain}/private/{key}"
                return f"https://{domain}/private/{key}"

            return f"https://{bucket}.s3.amazonaws.com/private/{key}"


class BankAccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = BankAccount
        fields = (
            "id",
            "bank_name",
            "account_title",
            "account_number",
            "iban",
            "instructions",
            "is_active",
            "created_at",
        )
        read_only_fields = ("id", "created_at")


class PaymentActionSerializer(serializers.Serializer):
    rejection_reason = serializers.CharField(required=False, allow_blank=True, default="")


class PaymentSerializer(serializers.ModelSerializer):
    bank_account = BankAccountSerializer(read_only=True)
    proof_receipt = serializers.SerializerMethodField()
    proof_receipt_key = serializers.CharField(source="proof_receipt", read_only=True)
    proof_receipt_url = serializers.SerializerMethodField()

    class Meta:
        model = Payment
        fields = (
            "id",
            "student",
            "course",
            "amount",
            "bank_account",
            "proof_receipt",
            "proof_receipt_key",
            "proof_receipt_url",
            "transaction_reference",
            "proof_note",
            "status",
            "approved_by",
            "approved_at",
            "rejection_reason",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "id",
            "student",
            "amount",
            "approved_by",
            "approved_at",
            "rejection_reason",
            "created_at",
            "updated_at",
        )

    def get_proof_receipt(self, obj):
        return get_private_url_from_key(obj.proof_receipt)

    def get_proof_receipt_url(self, obj):
        return get_private_url_from_key(obj.proof_receipt)

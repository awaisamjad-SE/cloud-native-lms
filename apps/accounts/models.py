import uuid
from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
	class Role(models.TextChoices):
		ADMIN = "admin", "Admin"
		STUDENT = "student", "Student"

	id = models.UUIDField(
		primary_key=True,
		default=uuid.uuid4,
		editable=False,
	)

	email = models.EmailField(unique=True, null=True, blank=True)

	role = models.CharField(
		max_length=20,
		choices=Role.choices,
		default=Role.STUDENT,
	)

	is_email_verified = models.BooleanField(default=False)

	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	def __str__(self) -> str:
		return f"{self.username} ({self.role})"


class UserProfile(models.Model):
	user = models.OneToOneField(
		"accounts.User",
		on_delete=models.CASCADE,
		related_name="profile",
	)

	profile_image = models.CharField(max_length=500, blank=True)
	phone_number = models.CharField(max_length=20, blank=True)
	bio = models.TextField(blank=True)

	def __str__(self) -> str:
		return f"Profile for {self.user.username}"

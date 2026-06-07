from django.conf import settings
from django.db import models
from django.utils.text import slugify


class Course(models.Model):
	class Status(models.TextChoices):
		DRAFT = "draft", "Draft"
		PUBLISHED = "published", "Published"
		ARCHIVED = "archived", "Archived"

	id = models.BigAutoField(primary_key=True)
	title = models.CharField(max_length=255)
	slug = models.SlugField(unique=True, max_length=300)
	description = models.TextField(blank=True)
	thumbnail = models.CharField(max_length=500, blank=True)
	price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
	category = models.CharField(max_length=120, blank=True)
	status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
	is_featured = models.BooleanField(default=False)
	created_by = models.ForeignKey(
		settings.AUTH_USER_MODEL,
		on_delete=models.SET_NULL,
		null=True,
		blank=True,
		related_name="created_courses",
	)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	class Meta:
		ordering = ("-created_at",)

	def save(self, *args, **kwargs):
		if not self.slug:
			self.slug = slugify(self.title)
		super().save(*args, **kwargs)

	def __str__(self):
		return self.title


class Lesson(models.Model):
	class LessonType(models.TextChoices):
		VIDEO = "video", "Video"
		DOCUMENT = "document", "Document"

	id = models.BigAutoField(primary_key=True)
	course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="lessons")
	title = models.CharField(max_length=255)
	description = models.TextField(blank=True)
	lesson_type = models.CharField(max_length=20, choices=LessonType.choices)
	# Full S3 key, e.g. public/previews/intro.mp4 or private/videos/module-1.mp4
	s3_key = models.CharField(max_length=500)
	is_preview = models.BooleanField(default=False)
	order = models.PositiveIntegerField(default=1)
	duration = models.PositiveIntegerField(default=0)
	created_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		ordering = ("order", "id")
		constraints = [
			models.UniqueConstraint(fields=["course", "order"], name="unique_lesson_order_per_course"),
		]

	def __str__(self):
		return f"{self.course.title} - {self.title}"

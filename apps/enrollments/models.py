from django.conf import settings
from django.db import models


class Enrollment(models.Model):
	id = models.BigAutoField(primary_key=True)
	student = models.ForeignKey(
		settings.AUTH_USER_MODEL,
		on_delete=models.CASCADE,
		related_name="enrollments",
	)
	course = models.ForeignKey(
		"courses.Course",
		on_delete=models.CASCADE,
		related_name="enrollments",
	)
	is_active = models.BooleanField(default=True)
	created_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		ordering = ("-created_at",)
		constraints = [
			models.UniqueConstraint(fields=["student", "course"], name="unique_student_course_enrollment"),
		]

	def __str__(self):
		return f"{self.student} -> {self.course}"

from django.conf import settings
from django.db import models


class LessonProgress(models.Model):
	id = models.BigAutoField(primary_key=True)
	student = models.ForeignKey(
		settings.AUTH_USER_MODEL,
		on_delete=models.CASCADE,
		related_name="lesson_progress",
	)
	lesson = models.ForeignKey(
		"courses.Lesson",
		on_delete=models.CASCADE,
		related_name="progress_records",
	)
	is_completed = models.BooleanField(default=False)
	completed_at = models.DateTimeField(null=True, blank=True)
	updated_at = models.DateTimeField(auto_now=True)

	class Meta:
		constraints = [
			models.UniqueConstraint(fields=["student", "lesson"], name="unique_student_lesson_progress"),
		]

	def __str__(self):
		return f"{self.student} - {self.lesson} - completed={self.is_completed}"

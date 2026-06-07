from django.conf import settings
from django.db import models


class BankAccount(models.Model):
	id = models.BigAutoField(primary_key=True)
	bank_name = models.CharField(max_length=120)
	account_title = models.CharField(max_length=120)
	account_number = models.CharField(max_length=80)
	iban = models.CharField(max_length=80, blank=True)
	instructions = models.TextField(blank=True)
	is_active = models.BooleanField(default=True)
	created_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		ordering = ("-created_at",)

	def __str__(self):
		return f"{self.bank_name} - {self.account_title}"


class Payment(models.Model):
	class Status(models.TextChoices):
		PENDING = "pending", "Pending"
		APPROVED = "approved", "Approved"
		REJECTED = "rejected", "Rejected"

	id = models.BigAutoField(primary_key=True)
	student = models.ForeignKey(
		settings.AUTH_USER_MODEL,
		on_delete=models.CASCADE,
		related_name="payments",
	)
	course = models.ForeignKey(
		"courses.Course",
		on_delete=models.CASCADE,
		related_name="payments",
	)
	amount = models.DecimalField(max_digits=10, decimal_places=2)
	bank_account = models.ForeignKey(
		"payments.BankAccount",
		on_delete=models.SET_NULL,
		null=True,
		blank=True,
		related_name="payments",
	)
	proof_receipt = models.CharField(max_length=500, blank=True)
	transaction_reference = models.CharField(max_length=120, blank=True)
	proof_note = models.TextField(blank=True)
	status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
	approved_by = models.ForeignKey(
		settings.AUTH_USER_MODEL,
		on_delete=models.SET_NULL,
		null=True,
		blank=True,
		related_name="approved_payments",
	)
	approved_at = models.DateTimeField(null=True, blank=True)
	rejection_reason = models.CharField(max_length=255, blank=True)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	class Meta:
		ordering = ("-created_at",)

	def __str__(self):
		return f"Payment {self.id} - {self.student} - {self.status}"

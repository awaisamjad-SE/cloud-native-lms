from django.contrib import admin

from .models import BankAccount, Payment


@admin.register(BankAccount)
class BankAccountAdmin(admin.ModelAdmin):
	list_display = ("id", "bank_name", "account_title", "account_number", "is_active", "created_at")
	list_filter = ("is_active", "bank_name")
	search_fields = ("bank_name", "account_title", "account_number", "iban")


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
	list_display = (
		"id",
		"student",
		"course",
		"amount",
		"status",
		"transaction_reference",
		"approved_by",
		"approved_at",
		"created_at",
	)
	list_filter = ("status", "created_at")
	search_fields = ("student__username", "student__email", "course__title", "transaction_reference")

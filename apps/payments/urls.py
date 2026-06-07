from django.urls import path

from .views import (
    AdminBankAccountDetailView,
    AdminBankAccountListCreateView,
    AdminPaymentApproveView,
    AdminPaymentListView,
    AdminPaymentRejectView,
    MyPaymentsView,
    OfflinePaymentSubmitView,
    PublicBankAccountListView,
)

app_name = "payments"

urlpatterns = [
    # Student/public endpoints
    path("payments/bank-accounts/", PublicBankAccountListView.as_view(), name="public_bank_accounts"),
    path("payments/offline/submit/", OfflinePaymentSubmitView.as_view(), name="offline_payment_submit"),
    path("payments/my/", MyPaymentsView.as_view(), name="my_payments"),

    # Admin endpoints
    path("admin/bank-accounts/", AdminBankAccountListCreateView.as_view(), name="admin_bank_accounts"),
    path("admin/bank-accounts/<int:pk>/", AdminBankAccountDetailView.as_view(), name="admin_bank_account_detail"),
    path("admin/payments/", AdminPaymentListView.as_view(), name="admin_payments"),
    path("admin/payments/<int:pk>/approve/", AdminPaymentApproveView.as_view(), name="admin_payment_approve"),
    path("admin/payments/<int:pk>/reject/", AdminPaymentRejectView.as_view(), name="admin_payment_reject"),
]

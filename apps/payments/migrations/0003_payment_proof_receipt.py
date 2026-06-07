from django.db import migrations, models


class Migration(migrations.Migration):


	dependencies = [
		("payments", "0002_bankaccount_rename_paid_at_payment_approved_at_and_more"),
	]

	operations = [
		migrations.AddField(
			model_name="payment",
			name="proof_receipt",
			field=models.CharField(blank=True, max_length=500),
		),
	]
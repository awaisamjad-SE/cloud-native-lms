from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0002_add_role'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='role',
            field=models.CharField(choices=[('student', 'Student'), ('admin', 'Admin')], default='student', max_length=16),
        ),
        migrations.AddField(
            model_name='user',
            name='is_email_verified',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='user',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, null=True),
        ),
        migrations.AddField(
            model_name='user',
            name='updated_at',
            field=models.DateTimeField(auto_now=True, null=True),
        ),
        migrations.AlterField(
            model_name='user',
            name='email',
            field=models.EmailField(unique=True, max_length=254),
        ),
        migrations.RemoveField(
            model_name='user',
            name='profile_image',
        ),
        migrations.CreateModel(
            name='UserProfile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('profile_image', models.CharField(blank=True, max_length=500)),
                ('phone_number', models.CharField(blank=True, max_length=20)),
                ('bio', models.TextField(blank=True)),
                ('user', models.OneToOneField(on_delete=models.deletion.CASCADE, related_name='profile', to='accounts.user')),
            ],
        ),
    ]

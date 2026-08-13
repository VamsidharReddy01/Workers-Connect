import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('workers', '0007_booking_location_permission_granted_and_more'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='DeviceToken',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('token', models.CharField(db_index=True, max_length=512, unique=True)),
                ('platform', models.CharField(
                    choices=[('android', 'Android'), ('ios', 'iOS'), ('web', 'Web')],
                    default='android',
                    max_length=10,
                )),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('user', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='device_tokens',
                    to=settings.AUTH_USER_MODEL,
                )),
            ],
            options={
                'ordering': ['-updated_at'],
            },
        ),
        migrations.AddIndex(
            model_name='devicetoken',
            index=models.Index(fields=['user', 'is_active'], name='notificatio_user_id_is_active_idx'),
        ),
        migrations.CreateModel(
            name='Notification',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('notification_type', models.CharField(
                    choices=[
                        ('JOB_REQUEST_RECEIVED', 'Job Request Received'),
                        ('JOB_ACCEPTED', 'Job Accepted'),
                        ('JOB_DECLINED', 'Job Declined'),
                        ('WORKER_ON_THE_WAY', 'Worker On The Way'),
                        ('JOB_STARTED', 'Job Started'),
                        ('JOB_COMPLETED', 'Job Completed'),
                        ('JOB_CANCELLED', 'Job Cancelled'),
                        ('NEW_MESSAGE', 'New Message'),
                        ('SYSTEM_NOTIFICATION', 'System Notification'),
                    ],
                    db_index=True,
                    max_length=40,
                )),
                ('title', models.CharField(max_length=255)),
                ('message', models.TextField()),
                ('data', models.JSONField(blank=True, default=dict)),
                ('is_read', models.BooleanField(db_index=True, default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('recipient', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='notifications',
                    to=settings.AUTH_USER_MODEL,
                )),
                ('related_booking', models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='notifications',
                    to='workers.booking',
                )),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        migrations.AddIndex(
            model_name='notification',
            index=models.Index(fields=['recipient', 'is_read'], name='notificatio_recipie_is_read_idx'),
        ),
        migrations.AddIndex(
            model_name='notification',
            index=models.Index(fields=['recipient', 'created_at'], name='notificatio_recipie_created_idx'),
        ),
    ]

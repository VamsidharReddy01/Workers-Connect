# Generated manually for the worker booking lifecycle.

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('workers', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Booking',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('service_category', models.CharField(max_length=100)),
                ('description', models.TextField(blank=True)),
                ('address', models.CharField(max_length=255)),
                ('scheduled_at', models.DateTimeField()),
                ('total_amount', models.DecimalField(decimal_places=2, max_digits=10)),
                ('status', models.CharField(choices=[('requested', 'Requested'), ('accepted', 'Accepted'), ('declined', 'Declined'), ('on_the_way', 'On The Way'), ('in_progress', 'In Progress'), ('completed', 'Completed'), ('cancelled', 'Cancelled')], db_index=True, default='requested', max_length=20)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('customer', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='customer_bookings', to=settings.AUTH_USER_MODEL)),
                ('worker', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='bookings', to='workers.workerprofile')),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        migrations.AddIndex(
            model_name='booking',
            index=models.Index(fields=['worker', 'status'], name='workers_boo_worker__4868fe_idx'),
        ),
        migrations.AddIndex(
            model_name='booking',
            index=models.Index(fields=['customer', 'status'], name='workers_boo_custome_2de3c6_idx'),
        ),
        migrations.AddIndex(
            model_name='booking',
            index=models.Index(fields=['scheduled_at'], name='workers_boo_schedul_04136b_idx'),
        ),
    ]

# Generated manually for worker bio and portfolio images.

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('workers', '0003_jobcategory'),
    ]

    operations = [
        migrations.AddField(
            model_name='workerprofile',
            name='bio',
            field=models.TextField(blank=True, default=''),
        ),
        migrations.CreateModel(
            name='WorkerWorkImage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('image', models.ImageField(upload_to='worker_portfolio/%Y/%m/')),
                ('caption', models.CharField(blank=True, default='', max_length=255)),
                ('sort_order', models.PositiveIntegerField(default=0)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('worker', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='work_images', to='workers.workerprofile')),
            ],
            options={
                'ordering': ['sort_order', '-created_at'],
            },
        ),
    ]

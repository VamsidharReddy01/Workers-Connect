from django.db import migrations, models


DEFAULT_CATEGORIES = [
    'Electrician',
    'Plumber',
    'Carpenter',
    'Painter',
    'House Cleaner',
    'AC Repair',
    'Mason',
    'Welder',
    'Gardener',
    'Pest Control',
]


def seed_job_categories(apps, schema_editor):
    JobCategory = apps.get_model('workers', 'JobCategory')
    JobCategory.objects.bulk_create(
        [
            JobCategory(name=name, sort_order=index, is_active=True)
            for index, name in enumerate(DEFAULT_CATEGORIES)
        ],
        ignore_conflicts=True,
    )


class Migration(migrations.Migration):

    dependencies = [
        ('workers', '0002_booking'),
    ]

    operations = [
        migrations.CreateModel(
            name='JobCategory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, unique=True)),
                ('sort_order', models.PositiveIntegerField(default=0)),
                ('is_active', models.BooleanField(default=True)),
            ],
            options={
                'verbose_name_plural': 'job categories',
                'ordering': ['sort_order', 'name'],
            },
        ),
        migrations.RunPython(seed_job_categories, migrations.RunPython.noop),
    ]

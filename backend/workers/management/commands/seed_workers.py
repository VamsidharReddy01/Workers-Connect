import secrets
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model
from django.conf import settings
from workers.models import WorkerProfile

User = get_user_model()


class Command(BaseCommand):
    help = 'Seeds sample workers and categories into the database (Development only)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force running the seed command even when DEBUG=False',
        )
        parser.add_argument(
            '--password',
            type=str,
            default=None,
            help='Explicit password for dev testing accounts (otherwise cryptographically random passwords will be generated)',
        )

    def handle(self, *args, **options):
        # SECURITY FIX #7: Prevent running in production environments
        if not settings.DEBUG and not options.get('force'):
            raise CommandError(
                'CRITICAL: seed_workers cannot be run in production (DEBUG=False). '
                'Pass --force if you understand the risks.'
            )

        self.stdout.write('Seeding sample workers...')

        default_password = options.get('password')

        workers_data = [
            {
                'username': 'Ramesh_Kumar',
                'email': 'ramesh@example.com',
                'phone_number': '9876543210',
                'location': 'Delhi',
                'category': 'Electrician',
                'price': 120.00,
                'rating': 4.8,
                'total_reviews': 120,
                'experience': 5
            },
            {
                'username': 'Suresh_Yadav',
                'email': 'suresh@example.com',
                'phone_number': '9876543211',
                'location': 'Mumbai',
                'category': 'Plumber',
                'price': 98.00,
                'rating': 4.6,
                'total_reviews': 98,
                'experience': 3
            },
            {
                'username': 'Dinesh_Sharma',
                'email': 'dinesh@example.com',
                'phone_number': '9876543212',
                'location': 'Bangalore',
                'category': 'Carpenter',
                'price': 150.00,
                'rating': 4.9,
                'total_reviews': 240,
                'experience': 8
            },
            {
                'username': 'Mahesh_Patel',
                'email': 'mahesh@example.com',
                'phone_number': '9876543213',
                'location': 'Ahmedabad',
                'category': 'Painter',
                'price': 85.00,
                'rating': 4.7,
                'total_reviews': 85,
                'experience': 4
            },
            {
                'username': 'Rajesh_Gupta',
                'email': 'rajesh@example.com',
                'phone_number': '9876543214',
                'location': 'Kolkata',
                'category': 'House Cleaner',
                'price': 60.00,
                'rating': 4.5,
                'total_reviews': 60,
                'experience': 2
            },
            {
                'username': 'Amit_Singh',
                'email': 'amit@example.com',
                'phone_number': '9876543215',
                'location': 'Noida',
                'category': 'AC Repair',
                'price': 110.00,
                'rating': 4.7,
                'total_reviews': 110,
                'experience': 5
            },
            {
                'username': 'Anil_Sharma',
                'email': 'anil@example.com',
                'phone_number': '9876543216',
                'location': 'Gurgaon',
                'category': 'Electrician',
                'price': 130.00,
                'rating': 4.9,
                'total_reviews': 150,
                'experience': 6
            },
            {
                'username': 'Sunil_Varma',
                'email': 'sunil@example.com',
                'phone_number': '9876543217',
                'location': 'Hyderabad',
                'category': 'Plumber',
                'price': 105.00,
                'rating': 4.8,
                'total_reviews': 115,
                'experience': 4
            }
        ]

        for data in workers_data:
            # Generate random password per user if not explicitly provided
            raw_password = default_password or secrets.token_urlsafe(16)

            # Create user if not exists
            user, created = User.objects.get_or_create(
                email=data['email'],
                defaults={
                    'username': data['username'],
                    'role': 'worker',
                    'phone_number': data['phone_number'],
                    'location': data['location']
                }
            )
            if created:
                user.set_password(raw_password)
                user.save()
                self.stdout.write(f"Created worker user: {user.username} (password: {raw_password})")
            else:
                user.username = data['username']
                user.role = 'worker'
                user.phone_number = data['phone_number']
                user.location = data['location']
                user.save()

            # Create or update profile
            profile, profile_created = WorkerProfile.objects.update_or_create(
                user=user,
                defaults={
                    'category': data['category'],
                    'price': data['price'],
                    'rating': data['rating'],
                    'total_reviews': data['total_reviews'],
                    'experience_years': data['experience']
                }
            )
            self.stdout.write(f"Seeded profile for {user.username} in {profile.category} (${profile.price}/hr)")

        self.stdout.write(self.style.SUCCESS('Successfully seeded all sample workers!'))

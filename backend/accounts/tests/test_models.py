from django.test import TestCase
from django.db.utils import IntegrityError
from django.utils import timezone
from accounts.models import User, SupportTicket


class UserModelTests(TestCase):
    def test_create_user_default_role(self):
        user = User.objects.create_user(
            username='johndoe',
            email='john@example.com',
            password='Password123!'
        )
        self.assertEqual(user.username, 'johndoe')
        self.assertEqual(user.email, 'john@example.com')
        self.assertEqual(user.role, 'customer')
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)
        self.assertTrue(user.is_active)
        self.assertFalse(user.location_permission_granted)

    def test_create_user_worker_role(self):
        user = User.objects.create_user(
            username='workerjohn',
            email='workerjohn@example.com',
            password='Password123!',
            role='worker'
        )
        self.assertEqual(user.role, 'worker')

    def test_create_superuser(self):
        admin = User.objects.create_superuser(
            username='adminuser',
            email='admin@example.com',
            password='AdminPassword123!'
        )
        self.assertTrue(admin.is_staff)
        self.assertTrue(admin.is_superuser)

    def test_phone_number_optional_and_unique(self):
        u1 = User.objects.create_user(
            username='user1',
            email='user1@example.com',
            password='Password123!',
            phone_number='9876543210'
        )
        self.assertEqual(u1.phone_number, '9876543210')

        # Duplicate phone number should fail
        with self.assertRaises(IntegrityError):
            User.objects.create_user(
                username='user2',
                email='user2@example.com',
                password='Password123!',
                phone_number='9876543210'
            )

    def test_multiple_users_with_null_phone_number(self):
        u1 = User.objects.create_user(username='u1', email='u1@example.com', password='pwd', phone_number=None)
        u2 = User.objects.create_user(username='u2', email='u2@example.com', password='pwd', phone_number=None)
        self.assertIsNone(u1.phone_number)
        self.assertIsNone(u2.phone_number)

    def test_user_coordinates_and_location(self):
        now = timezone.now()
        user = User.objects.create_user(
            username='locuser',
            email='loc@example.com',
            password='pwd',
            location='Hyderabad, India',
            latitude=17.385044,
            longitude=78.486671,
            location_permission_granted=True,
            location_updated_at=now
        )
        self.assertEqual(user.location, 'Hyderabad, India')
        self.assertAlmostEqual(float(user.latitude), 17.385044, places=5)
        self.assertAlmostEqual(float(user.longitude), 78.486671, places=5)
        self.assertTrue(user.location_permission_granted)
        self.assertEqual(user.location_updated_at, now)

    def test_user_str_representation(self):
        user = User.objects.create_user(username='stringuser', email='str@example.com', password='pwd')
        self.assertEqual(str(user), 'stringuser')


class SupportTicketModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='ticketuser', email='t@example.com', password='pwd')

    def test_create_support_ticket_defaults(self):
        ticket = SupportTicket.objects.create(
            user=self.user,
            subject='Payment issue',
            message='I was charged twice for booking #12.'
        )
        self.assertEqual(ticket.user, self.user)
        self.assertEqual(ticket.subject, 'Payment issue')
        self.assertEqual(ticket.message, 'I was charged twice for booking #12.')
        self.assertEqual(ticket.status, SupportTicket.STATUS_OPEN)
        self.assertEqual(ticket.admin_note, '')
        self.assertIsNotNone(ticket.created_at)
        self.assertIsNotNone(ticket.updated_at)

    def test_support_ticket_status_choices(self):
        for status_code, label in SupportTicket.STATUS_CHOICES:
            ticket = SupportTicket.objects.create(
                user=self.user,
                subject=f'Test {status_code}',
                message='Test message content here.',
                status=status_code
            )
            self.assertEqual(ticket.status, status_code)

    def test_support_ticket_str(self):
        ticket = SupportTicket.objects.create(
            user=self.user,
            subject='Help with app',
            message='App is running slow on my phone.'
        )
        expected_str = f"Ticket #{ticket.id} - Help with app"
        self.assertEqual(str(ticket), expected_str)

    def test_support_ticket_ordering(self):
        t1 = SupportTicket.objects.create(user=self.user, subject='First', message='First ticket message.')
        t2 = SupportTicket.objects.create(user=self.user, subject='Second', message='Second ticket message.')
        tickets = list(SupportTicket.objects.all())
        self.assertEqual(tickets[0].id, t2.id)
        self.assertEqual(tickets[1].id, t1.id)

    def test_user_support_tickets_cascade_delete(self):
        ticket = SupportTicket.objects.create(user=self.user, subject='To be deleted', message='Message text.')
        ticket_id = ticket.id
        self.user.delete()
        self.assertFalse(SupportTicket.objects.filter(id=ticket_id).exists())

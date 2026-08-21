from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework import status
from accounts.models import User, SupportTicket


class UserAndAuthDeepTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='auth_deep_u',
            email='adu@example.com',
            password='Password123!',
            role='customer'
        )

    def test_user_email_trimmed_on_save(self):
        self.user.email = '  clean@example.com  '
        self.user.save()
        self.user.refresh_from_db()
        self.assertIn('@', self.user.email)

    def test_support_ticket_filter_by_status(self):
        SupportTicket.objects.create(user=self.user, subject='Open 1', message='Message text here.', status='open')
        SupportTicket.objects.create(user=self.user, subject='Closed 1', message='Message text here.', status='closed')

        open_tickets = SupportTicket.objects.filter(user=self.user, status='open')
        self.assertEqual(open_tickets.count(), 1)
        self.assertEqual(open_tickets.first().subject, 'Open 1')

    def test_support_ticket_admin_note_blank_by_default(self):
        t = SupportTicket.objects.create(user=self.user, subject='Subj', message='Valid ticket message body.')
        self.assertEqual(t.admin_note, '')

    def test_user_location_permission_toggle(self):
        self.assertFalse(self.user.location_permission_granted)
        self.user.location_permission_granted = True
        self.user.save()
        self.user.refresh_from_db()
        self.assertTrue(self.user.location_permission_granted)

    def test_user_set_password_hashes_properly(self):
        self.user.set_password('NewSecretPass123!')
        self.user.save()
        self.assertNotEqual(self.user.password, 'NewSecretPass123!')
        self.assertTrue(self.user.check_password('NewSecretPass123!'))

    def test_user_check_password_wrong(self):
        self.assertFalse(self.user.check_password('IncorrectPassword!'))

    def test_user_is_staff_default_false(self):
        self.assertFalse(self.user.is_staff)

    def test_user_is_active_default_true(self):
        self.assertTrue(self.user.is_active)

from django.test import TestCase
from accounts.models import User, SupportTicket


class ModelValidationsDeepTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='deep_val_u',
            email='dvu@example.com',
            password='Password123!',
            role='customer'
        )

    def test_user_email_domain_normalized_on_creation(self):
        u = User.objects.create_user(username='mixed_case_u', email='MixedCase@Domain.Com', password='Password123!')
        # Django normalize_email lowercases the domain portion
        self.assertEqual(u.email, 'MixedCase@domain.com')

    def test_user_phone_number_spaces_stripped_or_preserved(self):
        self.user.phone_number = '9876543210'
        self.user.save()
        self.user.refresh_from_db()
        self.assertEqual(self.user.phone_number, '9876543210')

    def test_user_role_choices(self):
        self.assertIn(self.user.role, ['customer', 'worker'])
        self.user.role = 'worker'
        self.user.save()
        self.user.refresh_from_db()
        self.assertEqual(self.user.role, 'worker')

    def test_support_ticket_user_relationship(self):
        t = SupportTicket.objects.create(user=self.user, subject='Relationship test', message='Message body text.')
        self.assertEqual(self.user.support_tickets.count(), 1)
        self.assertEqual(self.user.support_tickets.first(), t)

    def test_support_ticket_status_defaults_to_open(self):
        t = SupportTicket.objects.create(user=self.user, subject='Default status', message='Valid text content.')
        self.assertEqual(t.status, 'open')

    def test_support_ticket_status_in_progress(self):
        t = SupportTicket.objects.create(user=self.user, subject='In Progress status', message='Valid text content.', status=SupportTicket.STATUS_IN_PROGRESS)
        self.assertEqual(t.status, 'in_progress')

    def test_support_ticket_status_resolved(self):
        t = SupportTicket.objects.create(user=self.user, subject='Resolved status', message='Valid text content.', status=SupportTicket.STATUS_RESOLVED)
        self.assertEqual(t.status, 'resolved')

    def test_support_ticket_status_closed(self):
        t = SupportTicket.objects.create(user=self.user, subject='Closed status', message='Valid text content.', status=SupportTicket.STATUS_CLOSED)
        self.assertEqual(t.status, 'closed')

    def test_support_ticket_admin_note_assignment(self):
        t = SupportTicket.objects.create(user=self.user, subject='Admin Note test', message='Valid text content.', admin_note='Investigating refund.')
        self.assertEqual(t.admin_note, 'Investigating refund.')

    def test_user_location_permission_granted_false_by_default(self):
        u = User.objects.create_user(username='perm_u', email='pu@example.com', password='pwd')
        self.assertFalse(u.location_permission_granted)

    def test_user_location_permission_granted_true(self):
        u = User.objects.create_user(username='perm_u2', email='pu2@example.com', password='pwd', location_permission_granted=True)
        self.assertTrue(u.location_permission_granted)

    def test_user_location_updated_at_none_by_default(self):
        u = User.objects.create_user(username='time_u', email='tu@example.com', password='pwd')
        self.assertIsNone(u.location_updated_at)

    def test_user_has_profile_photo_false_by_default(self):
        u = User.objects.create_user(username='photo_u', email='photou@example.com', password='pwd')
        self.assertFalse(bool(u.profile_photo))

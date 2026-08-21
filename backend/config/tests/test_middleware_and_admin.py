from django.test import TestCase
from django.contrib.admin.sites import site
from accounts.models import User, SupportTicket
from workers.models import JobCategory, WorkerProfile, WorkerWorkImage, Booking
from notifications.models import DeviceToken, Notification


class DjangoAdminRegistrationTests(TestCase):
    def test_all_models_registered_in_admin(self):
        registered_models = site._registry
        self.assertIn(User, registered_models)
        self.assertIn(SupportTicket, registered_models)
        self.assertIn(JobCategory, registered_models)
        self.assertIn(WorkerProfile, registered_models)
        self.assertIn(WorkerWorkImage, registered_models)
        self.assertIn(Booking, registered_models)
        self.assertIn(DeviceToken, registered_models)
        self.assertIn(Notification, registered_models)

    def test_admin_requires_staff_user(self):
        non_staff = User.objects.create_user(username='nostaff', email='ns@example.com', password='Password123!')
        self.client.force_login(non_staff)
        res = self.client.get('/admin/')
        # Should redirect to admin login
        self.assertEqual(res.status_code, 302)

    def test_admin_accessible_for_staff_user(self):
        staff = User.objects.create_superuser(username='superstaff', email='ss@example.com', password='Password123!')
        self.client.force_login(staff)
        res = self.client.get('/admin/')
        self.assertEqual(res.status_code, 200)

from django.test import TestCase
from accounts.models import User
from workers.models import Booking, WorkerProfile
from django.utils import timezone
from notifications.models import DeviceToken, Notification, NotificationType, Platform


class DeviceTokenModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='notif_user', email='nu@example.com', password='pwd')

    def test_create_device_token_defaults(self):
        token = DeviceToken.objects.create(
            user=self.user,
            token='sample_fcm_token_1234567890_abcdef',
            platform=Platform.ANDROID
        )
        self.assertEqual(token.user, self.user)
        self.assertEqual(token.platform, Platform.ANDROID)
        self.assertTrue(token.is_active)
        self.assertIn('notif_user — android', str(token))

    def test_device_token_unique_constraint(self):
        DeviceToken.objects.create(user=self.user, token='unique_token', platform=Platform.IOS)
        with self.assertRaises(Exception):
            DeviceToken.objects.create(user=self.user, token='unique_token', platform=Platform.WEB)


class NotificationModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='recipient_user', email='ru@example.com', password='pwd')
        self.worker_user = User.objects.create_user(username='w_notif', email='wn@example.com', password='pwd', role='worker')
        self.worker_profile = WorkerProfile.objects.create(user=self.worker_user, category='Plumber', price=40.00)
        self.booking = Booking.objects.create(
            customer=self.user,
            worker=self.worker_profile,
            service_category='Plumber',
            address='Home Address',
            scheduled_at=timezone.now(),
            total_amount=80.00
        )

    def test_create_notification(self):
        notif = Notification.objects.create(
            recipient=self.user,
            notification_type=NotificationType.JOB_ACCEPTED,
            title='Job Accepted',
            message='Your request was accepted by the worker.',
            related_booking=self.booking,
            data={'booking_id': str(self.booking.id)},
            is_read=False
        )
        self.assertEqual(notif.recipient, self.user)
        self.assertEqual(notif.notification_type, NotificationType.JOB_ACCEPTED)
        self.assertEqual(notif.related_booking, self.booking)
        self.assertFalse(notif.is_read)
        self.assertIn('[JOB_ACCEPTED] → recipient_user', str(notif))

    def test_notification_survives_booking_deletion(self):
        notif = Notification.objects.create(
            recipient=self.user,
            notification_type=NotificationType.JOB_COMPLETED,
            title='Job Completed',
            message='Work finished.',
            related_booking=self.booking
        )
        self.booking.delete()
        notif.refresh_from_db()
        self.assertIsNone(notif.related_booking)
        self.assertEqual(notif.title, 'Job Completed')

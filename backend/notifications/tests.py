"""
Tests for the notifications app.

Covers:
  - DeviceToken registration (create, upsert, multi-device)
  - DeviceToken deactivation on logout
  - Notification listing
  - Unread count
  - Mark single notification read
  - Mark all notifications read
  - NotificationService.send() does not raise on FCM failure
  - Job lifecycle notification helpers
"""

from unittest.mock import MagicMock, patch

from django.test import TestCase
from rest_framework.test import APIClient

from accounts.models import User
from notifications.models import DeviceToken, Notification, NotificationType
from notifications.services import NotificationService
from workers.models import Booking, WorkerProfile


# ─── Helpers ─────────────────────────────────────────────────────────────────

def make_customer(username='customer1', email='customer1@test.com', password='pass12345'):
    return User.objects.create_user(
        username=username, email=email, password=password, role='customer'
    )


def make_worker_user(username='worker1', email='worker1@test.com', password='pass12345'):
    return User.objects.create_user(
        username=username, email=email, password=password, role='worker'
    )


def make_worker_profile(user):
    return WorkerProfile.objects.create(user=user, category='Carpenter', price='200.00')


def make_booking(customer, worker_profile):
    from django.utils import timezone
    return Booking.objects.create(
        customer=customer,
        worker=worker_profile,
        service_category='Carpenter',
        description='Fix door',
        address='123 Main St',
        scheduled_at=timezone.now(),
        total_amount='200.00',
        status=Booking.STATUS_REQUESTED,
    )


def authed_client(user):
    from rest_framework_simplejwt.tokens import RefreshToken
    client = APIClient()
    refresh = RefreshToken.for_user(user)
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(refresh.access_token)}')
    return client


# ─── DeviceToken Tests ────────────────────────────────────────────────────────

class DeviceTokenRegisterTests(TestCase):
    def setUp(self):
        self.user = make_customer()
        self.client = authed_client(self.user)

    def test_register_new_token(self):
        resp = self.client.post(
            '/api/notifications/device-token/',
            {'token': 'fcm-token-abc', 'platform': 'android'},
            format='json',
        )
        self.assertEqual(resp.status_code, 201)
        self.assertTrue(DeviceToken.objects.filter(user=self.user, token='fcm-token-abc').exists())

    def test_register_updates_existing_token(self):
        DeviceToken.objects.create(user=self.user, token='old-token', platform='android')
        # Re-registering same token → 200
        resp = self.client.post(
            '/api/notifications/device-token/',
            {'token': 'old-token', 'platform': 'android'},
            format='json',
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(DeviceToken.objects.filter(token='old-token').count(), 1)

    def test_multiple_devices_allowed(self):
        self.client.post('/api/notifications/device-token/', {'token': 'token-a'}, format='json')
        self.client.post('/api/notifications/device-token/', {'token': 'token-b'}, format='json')
        self.assertEqual(DeviceToken.objects.filter(user=self.user).count(), 2)

    def test_empty_token_rejected(self):
        resp = self.client.post('/api/notifications/device-token/', {'token': ''}, format='json')
        self.assertEqual(resp.status_code, 400)

    def test_deactivate_token(self):
        DeviceToken.objects.create(user=self.user, token='tok', is_active=True)
        resp = self.client.delete(
            '/api/notifications/device-token/',
            {'token': 'tok'},
            format='json',
        )
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(DeviceToken.objects.get(token='tok').is_active)

    def test_unauthenticated_rejected(self):
        resp = APIClient().post(
            '/api/notifications/device-token/', {'token': 'abc'}, format='json'
        )
        self.assertEqual(resp.status_code, 401)


# ─── Notification List / Count Tests ─────────────────────────────────────────

class NotificationListTests(TestCase):
    def setUp(self):
        self.user = make_customer()
        self.client = authed_client(self.user)
        Notification.objects.create(
            recipient=self.user,
            notification_type=NotificationType.JOB_ACCEPTED,
            title='Accepted',
            message='Your job was accepted.',
        )
        Notification.objects.create(
            recipient=self.user,
            notification_type=NotificationType.JOB_COMPLETED,
            title='Done',
            message='Your job is done.',
            is_read=True,
        )

    def test_list_all_notifications(self):
        resp = self.client.get('/api/notifications/')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.data['list']), 2)

    def test_list_unread_only(self):
        resp = self.client.get('/api/notifications/?unread_only=true')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.data['list']), 1)

    def test_unread_count(self):
        resp = self.client.get('/api/notifications/unread-count/')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data['count'], 1)

    def test_mark_single_read(self):
        notif = Notification.objects.filter(recipient=self.user, is_read=False).first()
        resp = self.client.patch(f'/api/notifications/{notif.id}/read/')
        self.assertEqual(resp.status_code, 200)
        notif.refresh_from_db()
        self.assertTrue(notif.is_read)

    def test_mark_all_read(self):
        resp = self.client.post('/api/notifications/mark-all-read/')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(Notification.objects.filter(recipient=self.user, is_read=False).count(), 0)

    def test_other_user_cannot_see_notifications(self):
        other = make_customer('other', 'other@test.com')
        other_client = authed_client(other)
        resp = other_client.get('/api/notifications/')
        self.assertEqual(len(resp.data['list']), 0)

    def test_other_user_cannot_mark_read(self):
        notif = Notification.objects.filter(recipient=self.user).first()
        other = make_customer('other2', 'other2@test.com')
        other_client = authed_client(other)
        resp = other_client.patch(f'/api/notifications/{notif.id}/read/')
        self.assertEqual(resp.status_code, 404)


# ─── NotificationService Tests ───────────────────────────────────────────────

class NotificationServiceTests(TestCase):
    def setUp(self):
        self.customer = make_customer()
        self.worker_user = make_worker_user()
        self.worker = make_worker_profile(self.worker_user)
        self.booking = make_booking(self.customer, self.worker)

    @patch('notifications.services._send_fcm_to_tokens')
    def test_send_creates_notification_record(self, mock_fcm):
        NotificationService.send(
            recipient=self.customer,
            notification_type=NotificationType.JOB_ACCEPTED,
            title='Test',
            message='Test message',
            booking=self.booking,
        )
        self.assertEqual(
            Notification.objects.filter(
                recipient=self.customer,
                notification_type=NotificationType.JOB_ACCEPTED,
            ).count(),
            1,
        )

    @patch('notifications.services._send_fcm_to_tokens', side_effect=Exception('FCM down'))
    def test_fcm_failure_does_not_raise(self, mock_fcm):
        """FCM failure must not propagate to callers."""
        # If this raises, the test fails
        NotificationService.send(
            recipient=self.customer,
            notification_type=NotificationType.JOB_ACCEPTED,
            title='Test',
            message='Msg',
        )
        # Notification record still created
        self.assertTrue(
            Notification.objects.filter(recipient=self.customer).exists()
        )

    @patch('notifications.services._send_fcm_to_tokens')
    def test_notify_new_job_request_targets_worker(self, mock_fcm):
        NotificationService.notify_new_job_request(self.booking)
        notif = Notification.objects.get(notification_type=NotificationType.JOB_REQUEST_RECEIVED)
        self.assertEqual(notif.recipient, self.worker_user)

    @patch('notifications.services._send_fcm_to_tokens')
    def test_notify_job_accepted_targets_customer(self, mock_fcm):
        NotificationService.notify_job_accepted(self.booking)
        notif = Notification.objects.get(notification_type=NotificationType.JOB_ACCEPTED)
        self.assertEqual(notif.recipient, self.customer)

    @patch('notifications.services._send_fcm_to_tokens')
    def test_notify_job_declined_targets_customer(self, mock_fcm):
        NotificationService.notify_job_declined(self.booking)
        notif = Notification.objects.get(notification_type=NotificationType.JOB_DECLINED)
        self.assertEqual(notif.recipient, self.customer)

    @patch('notifications.services._send_fcm_to_tokens')
    def test_notify_completed_targets_customer(self, mock_fcm):
        NotificationService.notify_job_completed(self.booking)
        notif = Notification.objects.get(notification_type=NotificationType.JOB_COMPLETED)
        self.assertEqual(notif.recipient, self.customer)

    @patch('notifications.services._send_fcm_to_tokens')
    def test_duplicate_send_creates_two_records(self, mock_fcm):
        """Calling send() twice should create two DB records (dedup is caller's responsibility)."""
        NotificationService.notify_job_accepted(self.booking)
        NotificationService.notify_job_accepted(self.booking)
        self.assertEqual(
            Notification.objects.filter(
                notification_type=NotificationType.JOB_ACCEPTED
            ).count(),
            2,
        )

    @patch('notifications.services._send_fcm_to_tokens')
    def test_send_includes_booking_id_in_data(self, mock_fcm):
        NotificationService.notify_job_accepted(self.booking)
        notif = Notification.objects.get(notification_type=NotificationType.JOB_ACCEPTED)
        self.assertEqual(notif.data.get('booking_id'), str(self.booking.id))

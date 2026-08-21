from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from accounts.models import User
from notifications.models import Notification, NotificationType, DeviceToken


class NotificationViewsTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='view_notif_u', email='vnu@example.com', password='Password123!')

    def test_device_token_register_and_deactivate(self):
        self.client.force_authenticate(user=self.user)

        # Register
        res = self.client.post('/api/notifications/device-token/', {
            'token': 'fcm_device_token_abc_123',
            'platform': 'android'
        })
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertTrue(DeviceToken.objects.filter(user=self.user, token='fcm_device_token_abc_123', is_active=True).exists())

        # Deactivate
        del_res = self.client.delete('/api/notifications/device-token/', {
            'token': 'fcm_device_token_abc_123'
        })
        self.assertEqual(del_res.status_code, status.HTTP_200_OK)
        dt = DeviceToken.objects.get(user=self.user, token='fcm_device_token_abc_123')
        self.assertFalse(dt.is_active)

    def test_notification_list_and_unread_filter(self):
        Notification.objects.create(recipient=self.user, notification_type=NotificationType.JOB_ACCEPTED, title='T1', message='M1', is_read=False)
        Notification.objects.create(recipient=self.user, notification_type=NotificationType.JOB_COMPLETED, title='T2', message='M2', is_read=True)

        self.client.force_authenticate(user=self.user)

        # All notifications
        res1 = self.client.get('/api/notifications/')
        self.assertEqual(res1.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res1.data['list']), 2)

        # Unread only
        res2 = self.client.get('/api/notifications/?unread_only=true')
        self.assertEqual(res2.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res2.data['list']), 1)

    def test_unread_count_view(self):
        Notification.objects.create(recipient=self.user, notification_type=NotificationType.JOB_ACCEPTED, title='T1', message='M1', is_read=False)
        Notification.objects.create(recipient=self.user, notification_type=NotificationType.JOB_STARTED, title='T2', message='M2', is_read=False)

        self.client.force_authenticate(user=self.user)
        res = self.client.get('/api/notifications/unread-count/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['count'], 2)

    def test_mark_single_notification_read(self):
        notif = Notification.objects.create(recipient=self.user, notification_type=NotificationType.JOB_ACCEPTED, title='T1', message='M1', is_read=False)
        self.client.force_authenticate(user=self.user)

        res = self.client.patch(f'/api/notifications/{notif.id}/read/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        notif.refresh_from_db()
        self.assertTrue(notif.is_read)

    def test_mark_all_notifications_read(self):
        Notification.objects.create(recipient=self.user, notification_type=NotificationType.JOB_ACCEPTED, title='T1', message='M1', is_read=False)
        Notification.objects.create(recipient=self.user, notification_type=NotificationType.JOB_STARTED, title='T2', message='M2', is_read=False)

        self.client.force_authenticate(user=self.user)
        res = self.client.post('/api/notifications/mark-all-read/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['marked_read'], 2)
        self.assertEqual(Notification.objects.filter(recipient=self.user, is_read=False).count(), 0)

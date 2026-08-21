from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from accounts.models import User
from notifications.models import Notification, NotificationType, DeviceToken, Platform


class NotificationEdgeCasesTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user1 = User.objects.create_user(username='u1_notif', email='u1@example.com', password='Password123!')
        self.user2 = User.objects.create_user(username='u2_notif', email='u2@example.com', password='Password123!')

    def test_unread_count_isolated_per_user(self):
        # User 1 has 3 unread
        for i in range(3):
            Notification.objects.create(recipient=self.user1, notification_type=NotificationType.JOB_ACCEPTED, title=f'U1-{i}', message='msg', is_read=False)

        # User 2 has 1 unread
        Notification.objects.create(recipient=self.user2, notification_type=NotificationType.JOB_ACCEPTED, title='U2-1', message='msg', is_read=False)

        self.client.force_authenticate(user=self.user1)
        res1 = self.client.get('/api/notifications/unread-count/')
        self.assertEqual(res1.data['count'], 3)

        self.client.force_authenticate(user=self.user2)
        res2 = self.client.get('/api/notifications/unread-count/')
        self.assertEqual(res2.data['count'], 1)

    def test_cannot_mark_other_user_notification_read(self):
        n2 = Notification.objects.create(recipient=self.user2, notification_type=NotificationType.JOB_ACCEPTED, title='U2 Notif', message='msg', is_read=False)

        self.client.force_authenticate(user=self.user1)
        res = self.client.patch(f'/api/notifications/{n2.id}/read/')
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

    def test_mark_already_read_notification(self):
        n1 = Notification.objects.create(recipient=self.user1, notification_type=NotificationType.JOB_ACCEPTED, title='U1 Notif', message='msg', is_read=True)

        self.client.force_authenticate(user=self.user1)
        res = self.client.patch(f'/api/notifications/{n1.id}/read/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_mark_all_read_when_no_unread_exists(self):
        self.client.force_authenticate(user=self.user1)
        res = self.client.post('/api/notifications/mark-all-read/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['marked_read'], 0)

    def test_device_token_upsert_same_token_different_platform(self):
        self.client.force_authenticate(user=self.user1)
        # Register on android
        self.client.post('/api/notifications/device-token/', {'token': 'multi_platform_tok', 'platform': 'android'})
        # Upsert with ios
        res = self.client.post('/api/notifications/device-token/', {'token': 'multi_platform_tok', 'platform': 'ios'})
        self.assertIn(res.status_code, [status.HTTP_200_OK, status.HTTP_201_CREATED])
        dt = DeviceToken.objects.get(user=self.user1, token='multi_platform_tok')
        self.assertEqual(dt.platform, 'ios')

    def test_device_token_delete_all_tokens_when_token_omitted(self):
        DeviceToken.objects.create(user=self.user1, token='tok1', platform=Platform.ANDROID)
        DeviceToken.objects.create(user=self.user1, token='tok2', platform=Platform.IOS)

        self.client.force_authenticate(user=self.user1)
        res = self.client.delete('/api/notifications/device-token/', {})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(DeviceToken.objects.filter(user=self.user1, is_active=True).count(), 0)

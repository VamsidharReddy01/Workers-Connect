from django.test import TestCase
from accounts.models import User
from notifications.models import DeviceToken, Notification, NotificationType, Platform
from notifications.serializers import DeviceTokenSerializer, NotificationSerializer


class NotificationSerializerTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='ser_notif_user', email='snu@example.com', password='pwd')

    def test_device_token_serializer_valid(self):
        serializer = DeviceTokenSerializer(data={'token': 'valid_fcm_token_string', 'platform': 'android'})
        self.assertTrue(serializer.is_valid())

    def test_device_token_serializer_empty_token(self):
        serializer = DeviceTokenSerializer(data={'token': '   ', 'platform': 'ios'})
        self.assertFalse(serializer.is_valid())
        self.assertIn('token', serializer.errors)

    def test_notification_serializer_output(self):
        notif = Notification.objects.create(
            recipient=self.user,
            notification_type=NotificationType.SYSTEM_NOTIFICATION,
            title='Welcome!',
            message='Welcome to Workers Bridge Marketplace.',
            data={'info': 'welcome_package'},
            is_read=False
        )
        serializer = NotificationSerializer(notif)
        data = serializer.data
        self.assertEqual(data['id'], notif.id)
        self.assertEqual(data['title'], 'Welcome!')
        self.assertEqual(data['notification_type'], NotificationType.SYSTEM_NOTIFICATION)
        self.assertFalse(data['is_read'])

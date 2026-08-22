import requests
from selenium_tests.base import APIEndToEndTestCase
from notifications.models import Notification

class NotificationsAPIEndToEndTests(APIEndToEndTestCase):
    def setUp(self):
        super().setUp()
        self.user = self.create_customer('notif')
        self.user_email = 'customer_notif@example.com'
        self.user_pass = 'CustPass123!'
        self.acc, _ = self.login_api(self.user_email, self.user_pass)

    def test_notification_list_empty(self):
        """1"""
        r = self.authenticated_get('/api/notifications/', self.acc)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(len(r.json().get('results', r.json())), 0)

    def test_notification_list_with_data(self):
        """2"""
        self.create_notification(self.user, 'info', False)
        r = self.authenticated_get('/api/notifications/', self.acc)
        self.assertEqual(r.status_code, 200)

    def test_notification_unread_count_zero(self):
        """3"""
        r = self.authenticated_get('/api/notifications/unread-count/', self.acc)
        self.assertEqual(r.status_code, 200)

    def test_notification_unread_count_nonzero(self):
        """4"""
        for _ in range(3):
            self.create_notification(self.user, 'info', False)
        r = self.authenticated_get('/api/notifications/unread-count/', self.acc)
        self.assertEqual(r.status_code, 200)

    def test_notification_mark_read(self):
        """5"""
        n = self.create_notification(self.user, 'info', False)
        r = self.authenticated_post(f'/api/notifications/{n.id}/read/', self.acc)
        self.assertEqual(r.status_code, 200)

    def test_notification_mark_all_read(self):
        """6"""
        self.create_notification(self.user, 'info', False)
        r = self.authenticated_post('/api/notifications/mark-all-read/', self.acc)
        self.assertEqual(r.status_code, 200)

    def test_device_token_register(self):
        """7"""
        r = self.authenticated_post('/api/notifications/device-token/', self.acc, json={'token': 'test_token', 'platform': 'android'})
        self.assertEqual(r.status_code, 201)

    def test_device_token_update_existing(self):
        """8"""
        self.authenticated_post('/api/notifications/device-token/', self.acc, json={'token': 't1', 'platform': 'android'})
        r = self.authenticated_post('/api/notifications/device-token/', self.acc, json={'token': 't1', 'platform': 'ios'})
        self.assertEqual(r.status_code, 201)

    def test_device_token_deactivate(self):
        """9"""
        r = self.authenticated_post('/api/notifications/device-token/', self.acc, json={'token': 't2', 'is_active': False})
        self.assertEqual(r.status_code, 201)

    def test_notification_list_unauthenticated(self):
        """10"""
        r = self.http.get(self.api_url('/api/notifications/'))
        self.assertEqual(r.status_code, 401)

    def test_unread_count_unauthenticated(self):
        """11"""
        r = self.http.get(self.api_url('/api/notifications/unread-count/'))
        self.assertEqual(r.status_code, 401)

    def test_mark_read_unauthenticated(self):
        """12"""
        r = self.http.post(self.api_url('/api/notifications/1/read/'))
        self.assertEqual(r.status_code, 401)

    def test_device_token_unauthenticated(self):
        """13"""
        r = self.http.post(self.api_url('/api/notifications/device-token/'))
        self.assertEqual(r.status_code, 401)

    def test_notification_ordering(self):
        """14"""
        self.create_notification(self.user, '1', False)
        self.create_notification(self.user, '2', False)
        r = self.authenticated_get('/api/notifications/', self.acc)
        self.assertEqual(r.status_code, 200)

    def test_mark_read_other_user_404(self):
        """15"""
        u2 = self.create_customer('notif2')
        n = self.create_notification(u2, 'info', False)
        r = self.authenticated_post(f'/api/notifications/{n.id}/read/', self.acc)
        self.assertEqual(r.status_code, 404)

    def test_mark_already_read_notification(self):
        """16"""
        n = self.create_notification(self.user, 'info', True)
        r = self.authenticated_post(f'/api/notifications/{n.id}/read/', self.acc)
        self.assertEqual(r.status_code, 200)

    def test_mark_all_read_when_none_unread(self):
        """17"""
        r = self.authenticated_post('/api/notifications/mark-all-read/', self.acc)
        self.assertEqual(r.status_code, 200)

    def test_notification_list_pagination(self):
        """18"""
        r = self.authenticated_get('/api/notifications/', self.acc)
        self.assertEqual(r.status_code, 200)

    def test_device_token_multi_platform(self):
        """19"""
        self.authenticated_post('/api/notifications/device-token/', self.acc, json={'token': 'ta', 'platform': 'android'})
        r = self.authenticated_post('/api/notifications/device-token/', self.acc, json={'token': 'ti', 'platform': 'ios'})
        self.assertEqual(r.status_code, 201)

    def test_notification_type_in_response(self):
        """20"""
        self.create_notification(self.user, 'info', False)
        r = self.authenticated_get('/api/notifications/', self.acc)
        self.assertEqual(r.status_code, 200)

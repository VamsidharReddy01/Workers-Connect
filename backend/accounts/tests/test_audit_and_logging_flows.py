from django.test import TestCase
from django.core.cache import cache
from rest_framework.test import APIClient
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from accounts.models import User
from accounts.views import _get_client_ip


class AuditAndLoggingFlowsTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        cache.clear()
        self.user = User.objects.create_user(
            username='audit_u',
            email='audit@example.com',
            password='Password123!',
            role='customer'
        )

    def test_get_client_ip_direct(self):
        class DummyRequest:
            META = {'REMOTE_ADDR': '192.168.1.100'}
        ip = _get_client_ip(DummyRequest())
        self.assertEqual(ip, '192.168.1.100')

    def test_get_client_ip_forwarded_for(self):
        class DummyRequest:
            META = {
                'HTTP_X_FORWARDED_FOR': '203.0.113.195, 70.41.3.18, 150.172.238.178',
                'REMOTE_ADDR': '192.168.1.1'
            }
        ip = _get_client_ip(DummyRequest())
        self.assertEqual(ip, '203.0.113.195')

    def test_get_client_ip_empty_meta(self):
        class DummyRequest:
            META = {}
        ip = _get_client_ip(DummyRequest())
        self.assertEqual(ip, 'unknown')

    def test_successful_login_triggers_audit_log(self):
        with self.assertLogs('security', level='INFO') as cm:
            res = self.client.post('/api/auth/login/', {'email': 'audit@example.com', 'password': 'Password123!'})
            self.assertEqual(res.status_code, status.HTTP_200_OK)
            self.assertTrue(any('Login success user=audit_u' in msg for msg in cm.output))

    def test_failed_login_triggers_audit_warning(self):
        with self.assertLogs('security', level='WARNING') as cm:
            res = self.client.post('/api/auth/login/', {'email': 'audit@example.com', 'password': 'WrongPassword!'})
            self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
            self.assertTrue(any('Login failed email=audit@example.com' in msg for msg in cm.output))

    def test_password_change_triggers_audit_log(self):
        self.client.force_authenticate(user=self.user)
        with self.assertLogs('security', level='INFO') as cm:
            res = self.client.post('/api/auth/change-password/', {
                'old_password': 'Password123!',
                'new_password': 'NewPassword123!',
                'confirm_password': 'NewPassword123!'
            })
            self.assertEqual(res.status_code, status.HTTP_200_OK)
            self.assertTrue(any('Password changed user=audit_u' in msg for msg in cm.output))

    def test_logout_triggers_audit_log(self):
        self.client.force_authenticate(user=self.user)
        refresh = RefreshToken.for_user(self.user)
        with self.assertLogs('security', level='INFO') as cm:
            res = self.client.post('/api/auth/logout/', {'refresh': str(refresh)})
            self.assertEqual(res.status_code, status.HTTP_200_OK)
            self.assertTrue(any('Logout user=audit_u' in msg for msg in cm.output))

    def test_signup_otp_dispatch_triggers_audit_log(self):
        with self.assertLogs('security', level='INFO') as cm:
            res = self.client.post('/api/auth/signup/send-otp/', {'email': 'brand_new@example.com'})
            self.assertEqual(res.status_code, status.HTTP_200_OK)
            self.assertTrue(any('OTP sent to email=brand_new@example.com' in msg for msg in cm.output))

    def test_signup_existing_email_otp_triggers_audit_log(self):
        with self.assertLogs('security', level='INFO') as cm:
            res = self.client.post('/api/auth/signup/send-otp/', {'email': 'audit@example.com'})
            self.assertEqual(res.status_code, status.HTTP_200_OK)
            self.assertTrue(any('OTP requested for existing email=audit@example.com' in msg for msg in cm.output))

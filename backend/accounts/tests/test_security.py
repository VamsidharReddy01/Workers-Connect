from django.test import TestCase
from django.core.cache import cache
from rest_framework.test import APIClient
from rest_framework import status
from accounts.models import User
from accounts.serializers import PublicUserSerializer


class AccountSecurityTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        cache.clear()
        self.user = User.objects.create_user(
            username='secuser',
            email='secuser@example.com',
            password='ComplexPassword123!',
            role='customer',
            phone_number='9876500000',
            location='Secured Zone'
        )

    def test_signup_otp_user_enumeration_prevention(self):
        # Existing email
        res1 = self.client.post('/api/auth/signup/send-otp/', {'email': 'secuser@example.com'})
        self.assertEqual(res1.status_code, status.HTTP_200_OK)
        self.assertEqual(res1.data['message'], 'If this email is eligible, an OTP has been sent.')

        # Non-existing email
        res2 = self.client.post('/api/auth/signup/send-otp/', {'email': 'unregistered@example.com'})
        self.assertEqual(res2.status_code, status.HTTP_200_OK)
        self.assertEqual(res2.data['message'], 'If this email is eligible, an OTP has been sent.')

    def test_role_self_assignment_prevention(self):
        cache.set('signup_email_otp:escalator@example.com', '123456', timeout=600)
        cache.set('signup_otp_attempts:escalator@example.com', 0, timeout=600)

        payload = {
            'username': 'escalator',
            'email': 'escalator@example.com',
            'password': 'StrongPassword123!',
            'role': 'worker',
            'email_otp': '123456',
        }
        res = self.client.post('/api/auth/signup/', payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        created_user = User.objects.get(email='escalator@example.com')
        self.assertEqual(created_user.role, 'customer')

    def test_otp_brute_force_lockout(self):
        cache.set('signup_email_otp:victim@example.com', '999999', timeout=600)
        cache.set('signup_otp_attempts:victim@example.com', 0, timeout=600)

        payload = {
            'username': 'victim',
            'email': 'victim@example.com',
            'password': 'StrongPassword123!',
            'email_otp': '000000',
        }

        for _ in range(5):
            res = self.client.post('/api/auth/signup/', payload)
            self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

        # 6th attempt triggers lockout and cache purge
        res = self.client.post('/api/auth/signup/', payload)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Too many failed attempts', str(res.data))
        self.assertIsNone(cache.get('signup_email_otp:victim@example.com'))

    def test_public_user_serializer_omits_pii(self):
        serializer = PublicUserSerializer(self.user)
        data = serializer.data
        self.assertNotIn('email', data)
        self.assertNotIn('phone_number', data)
        self.assertNotIn('latitude', data)
        self.assertNotIn('longitude', data)
        self.assertEqual(data['username'], 'secuser')

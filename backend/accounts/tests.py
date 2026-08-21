from django.test import TestCase
from django.core.cache import cache
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from .models import User
from .serializers import PublicUserSerializer, UserSerializer


class SecurityAuthTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        cache.clear()
        self.user = User.objects.create_user(
            username='testuser',
            email='testuser@example.com',
            password='Password123!',
            role='customer',
            phone_number='1234567890',
            location='Test City'
        )

    def test_signup_otp_user_enumeration_prevention(self):
        """Fix #11: Ensure send-otp returns same response whether email exists or not."""
        # Existing email
        res1 = self.client.post('/api/auth/signup/send-otp/', {'email': 'testuser@example.com'})
        self.assertEqual(res1.status_code, status.HTTP_200_OK)
        self.assertEqual(res1.data['message'], 'If this email is eligible, an OTP has been sent.')

        # Non-existing email
        res2 = self.client.post('/api/auth/signup/send-otp/', {'email': 'newuser@example.com'})
        self.assertEqual(res2.status_code, status.HTTP_200_OK)
        self.assertEqual(res2.data['message'], 'If this email is eligible, an OTP has been sent.')

    def test_role_self_assignment_prevention(self):
        """Fix #8: Ensure user cannot escalate privilege to worker or admin during signup."""
        cache.set('signup_email_otp:attacker@example.com', '123456', timeout=600)
        cache.set('signup_otp_attempts:attacker@example.com', 0, timeout=600)

        payload = {
            'username': 'attacker',
            'email': 'attacker@example.com',
            'password': 'StrongPassword123!',
            'role': 'worker',  # Attempt privilege escalation
            'email_otp': '123456',
        }
        res = self.client.post('/api/auth/signup/', payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        created_user = User.objects.get(email='attacker@example.com')
        # Role must remain customer
        self.assertEqual(created_user.role, 'customer')

    def test_otp_brute_force_lockout(self):
        """Fix #10: Ensure OTP is invalidated after 5 failed attempts."""
        cache.set('signup_email_otp:victim@example.com', '999999', timeout=600)
        cache.set('signup_otp_attempts:victim@example.com', 0, timeout=600)

        payload = {
            'username': 'victim',
            'email': 'victim@example.com',
            'password': 'StrongPassword123!',
            'email_otp': '000000',  # Wrong OTP
        }

        for i in range(5):
            res = self.client.post('/api/auth/signup/', payload)
            self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

        # 6th attempt should trigger lockout message and invalidate the OTP
        res = self.client.post('/api/auth/signup/', payload)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Too many failed attempts', str(res.data))
        self.assertIsNone(cache.get('signup_email_otp:victim@example.com'))

    def test_public_user_serializer_masks_sensitive_data(self):
        """Fix #20: Ensure PublicUserSerializer masks email and phone number."""
        serializer = PublicUserSerializer(self.user)
        data = serializer.data
        self.assertNotIn('email', data)
        self.assertNotIn('phone_number', data)
        self.assertNotIn('latitude', data)
        self.assertNotIn('longitude', data)
        self.assertEqual(data['username'], 'testuser')

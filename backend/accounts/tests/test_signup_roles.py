from decimal import Decimal
from django.core.cache import cache
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from accounts.models import User
from workers.models import WorkerProfile


class SignupRoleEndpointsTest(TestCase):
    """Tests for Worker vs Customer signup APIs and profile generation."""

    def setUp(self):
        self.client = APIClient()

    def test_customer_signup_endpoint_creates_customer_only(self):
        cache.set('signup_email_otp:new_customer@example.com', '123456', timeout=600)
        cache.set('signup_otp_attempts:new_customer@example.com', 0, timeout=600)

        payload = {
            'username': 'john_customer',
            'email': 'new_customer@example.com',
            'password': 'Password123!',
            'location': 'Madhapur, Hyderabad',
            'email_otp': '123456',
        }
        res = self.client.post('/api/auth/customer-signup/', payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        user = User.objects.get(email='new_customer@example.com')
        self.assertEqual(user.role, 'customer')
        self.assertEqual(user.username, 'john_customer')
        self.assertFalse(WorkerProfile.objects.filter(user=user).exists())

    def test_worker_signup_endpoint_creates_worker_and_profile(self):
        cache.set('signup_email_otp:pro_plumber@example.com', '654321', timeout=600)
        cache.set('signup_otp_attempts:pro_plumber@example.com', 0, timeout=600)

        payload = {
            'username': 'ramesh_plumber',
            'email': 'pro_plumber@example.com',
            'password': 'Password123!',
            'category': 'Plumber',
            'location': 'Kukatpally, Hyderabad',
            'latitude': 17.4875,
            'longitude': 78.4158,
            'email_otp': '654321',
        }
        res = self.client.post('/api/auth/worker-signup/', payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        user = User.objects.get(email='pro_plumber@example.com')
        self.assertEqual(user.role, 'worker')
        self.assertEqual(user.username, 'ramesh_plumber')

        # Check WorkerProfile creation
        profile = WorkerProfile.objects.get(user=user)
        self.assertEqual(profile.category, 'Plumber')
        self.assertTrue(profile.is_online)

    def test_general_signup_with_explicit_worker_role(self):
        cache.set('signup_email_otp:general_worker@example.com', '112233', timeout=600)
        cache.set('signup_otp_attempts:general_worker@example.com', 0, timeout=600)

        payload = {
            'username': 'sita_cleaner',
            'email': 'general_worker@example.com',
            'password': 'Password123!',
            'role': 'worker',
            'category': 'House Cleaner',
            'email_otp': '112233',
        }
        res = self.client.post('/api/auth/signup/', payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        user = User.objects.get(email='general_worker@example.com')
        self.assertEqual(user.role, 'worker')
        profile = WorkerProfile.objects.get(user=user)
        self.assertEqual(profile.category, 'House Cleaner')

    def test_nested_signup_routes(self):
        cache.set('signup_email_otp:nested_worker@example.com', '998877', timeout=600)
        cache.set('signup_otp_attempts:nested_worker@example.com', 0, timeout=600)

        res_worker = self.client.post('/api/auth/signup/worker/', {
            'username': 'nested_worker',
            'email': 'nested_worker@example.com',
            'password': 'Password123!',
            'category': 'Carpenter',
            'email_otp': '998877',
        })
        self.assertEqual(res_worker.status_code, status.HTTP_201_CREATED)
        self.assertEqual(User.objects.get(email='nested_worker@example.com').role, 'worker')

        cache.set('signup_email_otp:nested_cust@example.com', '554433', timeout=600)
        cache.set('signup_otp_attempts:nested_cust@example.com', 0, timeout=600)

        res_cust = self.client.post('/api/auth/signup/customer/', {
            'username': 'nested_cust',
            'email': 'nested_cust@example.com',
            'password': 'Password123!',
            'email_otp': '554433',
        })
        self.assertEqual(res_cust.status_code, status.HTTP_201_CREATED)
        self.assertEqual(User.objects.get(email='nested_cust@example.com').role, 'customer')

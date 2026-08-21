from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from accounts.models import User


class ApiContractTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='contract_u',
            email='contract@example.com',
            password='Password123!',
            role='customer'
        )

    def test_unauthenticated_endpoints_return_401_json(self):
        protected_endpoints = [
            ('GET', '/api/auth/profile/'),
            ('POST', '/api/auth/change-password/'),
            ('GET', '/api/auth/support/tickets/'),
            ('POST', '/api/auth/logout/'),
            ('GET', '/api/workers/profile/'),
            ('GET', '/api/workers/bookings/'),
            ('GET', '/api/workers/conversations/'),
            ('GET', '/api/notifications/'),
            ('GET', '/api/notifications/unread-count/'),
        ]
        for method, endpoint in protected_endpoints:
            with self.subTest(endpoint=endpoint):
                if method == 'GET':
                    res = self.client.get(endpoint)
                else:
                    res = self.client.post(endpoint, {})
                self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)
                self.assertIn('detail', res.data)

    def test_public_endpoints_accessible_without_auth(self):
        public_endpoints = [
            '/api/workers/categories/',
            '/api/workers/job-categories/',
            '/api/workers/nearby/',
        ]
        for endpoint in public_endpoints:
            with self.subTest(endpoint=endpoint):
                res = self.client.get(endpoint)
                self.assertEqual(res.status_code, status.HTTP_200_OK)
                self.assertIn('list', res.data)

    def test_security_headers_present_in_responses(self):
        res = self.client.get('/api/workers/categories/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.headers.get('X-Frame-Options'), 'DENY')
        self.assertEqual(res.headers.get('X-Content-Type-Options'), 'nosniff')

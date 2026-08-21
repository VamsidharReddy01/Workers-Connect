from django.test import TestCase
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from rest_framework.test import APIClient
from rest_framework import status
from accounts.models import User


class SecurityThrottlesAndHeadersTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='throttle_user',
            email='throttle@example.com',
            password='ComplexPassword123!',
            role='customer'
        )

    def test_password_validator_min_length(self):
        with self.assertRaises(ValidationError):
            validate_password('short', user=self.user)

    def test_password_validator_common_password_rejected(self):
        with self.assertRaises(ValidationError):
            validate_password('password123', user=self.user)

    def test_password_validator_numeric_only_rejected(self):
        with self.assertRaises(ValidationError):
            validate_password('123456789012', user=self.user)

    def test_password_validator_similar_to_username_rejected(self):
        with self.assertRaises(ValidationError):
            validate_password('throttle_user123', user=self.user)

    def test_password_validator_complex_password_accepted(self):
        # Should not raise
        validate_password('Kj9#mP2$xL7!vQ9@', user=self.user)

    def test_csp_header_in_response(self):
        res = self.client.get('/api/workers/categories/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        # Verify Content-Security-Policy or X-Frame-Options
        self.assertEqual(res.headers.get('X-Frame-Options'), 'DENY')
        self.assertEqual(res.headers.get('X-Content-Type-Options'), 'nosniff')

    def test_invalid_bearer_token_rejected(self):
        self.client.credentials(HTTP_AUTHORIZATION='Bearer InvalidMalformedJWTToken.Payload.Signature')
        res = self.client.get('/api/auth/profile/')
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_empty_bearer_token_rejected(self):
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ')
        res = self.client.get('/api/auth/profile/')
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_basic_auth_scheme_not_accepted(self):
        self.client.credentials(HTTP_AUTHORIZATION='Basic dXNlcjpwYXNzd29yZA==')
        res = self.client.get('/api/auth/profile/')
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

from django.test import TestCase
from django.core.cache import cache
from rest_framework.test import APIClient
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from accounts.models import User, SupportTicket


class AccountViewsTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        cache.clear()
        self.user = User.objects.create_user(
            username='mainuser',
            email='mainuser@example.com',
            password='ValidPassword123!',
            role='customer',
            phone_number='9876543210',
            location='Hyderabad'
        )

    def test_send_signup_otp_valid_email(self):
        res = self.client.post('/api/auth/signup/send-otp/', {'email': 'fresh@example.com'})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn('message', res.data)
        # Check OTP is stored in cache
        cached_otp = cache.get('signup_email_otp:fresh@example.com')
        self.assertIsNotNone(cached_otp)
        self.assertEqual(len(cached_otp), 6)

    def test_send_signup_otp_empty_email(self):
        res = self.client.post('/api/auth/signup/send-otp/', {'email': ''})
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', res.data['errors'])

    def test_send_signup_otp_invalid_email_format(self):
        res = self.client.post('/api/auth/signup/send-otp/', {'email': 'not-an-email'})
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', res.data['errors'])

    def test_signup_view_success(self):
        cache.set('signup_email_otp:newreg@example.com', '123456', timeout=600)
        cache.set('signup_otp_attempts:newreg@example.com', 0, timeout=600)

        payload = {
            'username': 'newreg',
            'email': 'newreg@example.com',
            'password': 'SecurePassword123!',
            'email_otp': '123456',
            'phone_number': '9123456780',
            'location': 'Mumbai'
        }
        res = self.client.post('/api/auth/signup/', payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertIn('access', res.data)
        self.assertIn('refresh', res.data)
        self.assertIn('user', res.data)
        self.assertEqual(res.data['user']['username'], 'newreg')
        # Cache should be cleared after successful signup
        self.assertIsNone(cache.get('signup_email_otp:newreg@example.com'))

    def test_login_view_success(self):
        payload = {'email': 'mainuser@example.com', 'password': 'ValidPassword123!'}
        res = self.client.post('/api/auth/login/', payload)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn('access', res.data)
        self.assertIn('refresh', res.data)
        self.assertEqual(res.data['user']['username'], 'mainuser')

    def test_login_view_invalid_credentials(self):
        payload = {'email': 'mainuser@example.com', 'password': 'WrongPassword!'}
        res = self.client.post('/api/auth/login/', payload)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('errors', res.data)

    def test_user_profile_get_authenticated(self):
        self.client.force_authenticate(user=self.user)
        res = self.client.get('/api/auth/profile/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['username'], 'mainuser')
        self.assertEqual(res.data['email'], 'mainuser@example.com')

    def test_user_profile_get_unauthenticated(self):
        res = self.client.get('/api/auth/profile/')
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_user_profile_patch_update(self):
        self.client.force_authenticate(user=self.user)
        res = self.client.patch('/api/auth/profile/', {'location': 'Bangalore'})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['location'], 'Bangalore')
        self.user.refresh_from_db()
        self.assertEqual(self.user.location, 'Bangalore')

    def test_change_password_view_success(self):
        self.client.force_authenticate(user=self.user)
        payload = {
            'old_password': 'ValidPassword123!',
            'new_password': 'NewPassword123!',
            'confirm_password': 'NewPassword123!'
        }
        res = self.client.post('/api/auth/change-password/', payload)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('NewPassword123!'))

    def test_change_password_view_unauthenticated(self):
        res = self.client.post('/api/auth/change-password/', {})
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_support_ticket_list_and_create(self):
        self.client.force_authenticate(user=self.user)

        # Create
        create_res = self.client.post('/api/auth/support/tickets/', {
            'subject': 'App Feedback',
            'message': 'Great application for booking skilled workers!'
        })
        self.assertEqual(create_res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(create_res.data['subject'], 'App Feedback')

        # List
        list_res = self.client.get('/api/auth/support/tickets/')
        self.assertEqual(list_res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(list_res.data['list']), 1)

    def test_support_ticket_user_isolation(self):
        other_user = User.objects.create_user(username='other', email='o@example.com', password='pwd')
        SupportTicket.objects.create(user=other_user, subject='Other Ticket', message='Other message content.')

        self.client.force_authenticate(user=self.user)
        res = self.client.get('/api/auth/support/tickets/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data['list']), 0)

    def test_logout_view_with_valid_refresh_token(self):
        self.client.force_authenticate(user=self.user)
        refresh = RefreshToken.for_user(self.user)
        res = self.client.post('/api/auth/logout/', {'refresh': str(refresh)})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['message'], 'Logged out successfully')

    def test_logout_view_missing_refresh_token(self):
        self.client.force_authenticate(user=self.user)
        res = self.client.post('/api/auth/logout/', {})
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_token_refresh_endpoint(self):
        refresh = RefreshToken.for_user(self.user)
        res = self.client.post('/api/auth/token/refresh/', {'refresh': str(refresh)})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn('access', res.data)

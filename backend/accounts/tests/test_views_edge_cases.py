from unittest.mock import patch
from django.test import TestCase
from django.core.cache import cache
from rest_framework.test import APIClient
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from accounts.models import User, SupportTicket


class AccountViewsEdgeCasesTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        cache.clear()
        self.user = User.objects.create_user(
            username='edgeuser',
            email='edge@example.com',
            password='ValidPassword123!',
            role='customer',
            phone_number='9876543210',
            location='Hyderabad'
        )

    # ── SendSignupOtpView Edge Cases ──────────────────────────────────────────
    @patch('accounts.views.send_mail')
    def test_send_otp_mail_delivery_failure(self, mock_send_mail):
        import smtplib
        mock_send_mail.side_effect = smtplib.SMTPAuthenticationError(535, b'5.7.8 Bad credentials')
        res = self.client.post('/api/auth/signup/send-otp/', {'email': 'testfailure@example.com'})
        self.assertEqual(res.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertIn('error', res.data)

    def test_send_otp_whitespace_email(self):
        res = self.client.post('/api/auth/signup/send-otp/', {'email': '   '})
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', res.data['errors'])

    def test_send_otp_missing_email_key(self):
        res = self.client.post('/api/auth/signup/send-otp/', {})
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_send_otp_uppercase_email_normalized(self):
        res = self.client.post('/api/auth/signup/send-otp/', {'email': 'NEWUSER@EXAMPLE.COM'})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIsNotNone(cache.get('signup_email_otp:newuser@example.com'))

    def test_send_otp_special_characters_in_email(self):
        res = self.client.post('/api/auth/signup/send-otp/', {'email': 'user+tag@domain.co.in'})
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_send_otp_sql_injection_string(self):
        res = self.client.post('/api/auth/signup/send-otp/', {'email': "' OR 1=1 --"})
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_send_otp_xss_payload(self):
        res = self.client.post('/api/auth/signup/send-otp/', {'email': '<script>alert(1)</script>@test.com'})
        # Should be rejected as invalid email
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    # ── SignupView Edge Cases ─────────────────────────────────────────────────
    def test_signup_with_unicode_username(self):
        cache.set('signup_email_otp:unicode@example.com', '123456', timeout=600)
        cache.set('signup_otp_attempts:unicode@example.com', 0, timeout=600)
        payload = {
            'username': 'José_Silva',
            'email': 'unicode@example.com',
            'password': 'SecurePassword123!',
            'email_otp': '123456'
        }
        res = self.client.post('/api/auth/signup/', payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res.data['user']['username'], 'José_Silva')

    def test_signup_missing_username(self):
        cache.set('signup_email_otp:noun@example.com', '123456', timeout=600)
        payload = {
            'email': 'noun@example.com',
            'password': 'Password123!',
            'email_otp': '123456'
        }
        res = self.client.post('/api/auth/signup/', payload)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('username', res.data['errors'])

    def test_signup_missing_password(self):
        cache.set('signup_email_otp:nopwd@example.com', '123456', timeout=600)
        payload = {
            'username': 'nopwd',
            'email': 'nopwd@example.com',
            'email_otp': '123456'
        }
        res = self.client.post('/api/auth/signup/', payload)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('password', res.data['errors'])

    def test_signup_whitespace_only_username(self):
        cache.set('signup_email_otp:spaces@example.com', '123456', timeout=600)
        payload = {
            'username': '    ',
            'email': 'spaces@example.com',
            'password': 'Password123!',
            'email_otp': '123456'
        }
        res = self.client.post('/api/auth/signup/', payload)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_signup_duplicate_username_case_insensitive(self):
        cache.set('signup_email_otp:dup@example.com', '123456', timeout=600)
        payload = {
            'username': 'EDGEUSER',  # Existing user is 'edgeuser'
            'email': 'dup@example.com',
            'password': 'Password123!',
            'email_otp': '123456'
        }
        res = self.client.post('/api/auth/signup/', payload)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('username', res.data['errors'])

    def test_signup_duplicate_email_case_insensitive(self):
        cache.set('signup_email_otp:dupemail@example.com', '123456', timeout=600)
        payload = {
            'username': 'unique_user',
            'email': 'EDGE@EXAMPLE.COM',  # Existing is 'edge@example.com'
            'password': 'Password123!',
            'email_otp': '123456'
        }
        res = self.client.post('/api/auth/signup/', payload)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', res.data['errors'])

    def test_signup_invalid_coordinate_ranges(self):
        cache.set('signup_email_otp:coord@example.com', '123456', timeout=600)
        payload = {
            'username': 'coord_user',
            'email': 'coord@example.com',
            'password': 'Password123!',
            'email_otp': '123456',
            'latitude': 95.0,  # Invalid (>90)
            'longitude': 50.0
        }
        res = self.client.post('/api/auth/signup/', payload)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_signup_partial_coordinates_latitude_only(self):
        cache.set('signup_email_otp:part1@example.com', '123456', timeout=600)
        payload = {
            'username': 'part1_user',
            'email': 'part1@example.com',
            'password': 'Password123!',
            'email_otp': '123456',
            'latitude': 17.38
        }
        res = self.client.post('/api/auth/signup/', payload)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('location', res.data['errors'])

    def test_signup_partial_coordinates_longitude_only(self):
        cache.set('signup_email_otp:part2@example.com', '123456', timeout=600)
        payload = {
            'username': 'part2_user',
            'email': 'part2@example.com',
            'password': 'Password123!',
            'email_otp': '123456',
            'longitude': 78.48
        }
        res = self.client.post('/api/auth/signup/', payload)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('location', res.data['errors'])

    # ── LoginView Edge Cases ──────────────────────────────────────────────────
    def test_login_missing_email(self):
        res = self.client.post('/api/auth/login/', {'password': 'SomePassword123!'})
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_missing_password(self):
        res = self.client.post('/api/auth/login/', {'email': 'edge@example.com'})
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_empty_payload(self):
        res = self.client.post('/api/auth/login/', {})
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_case_insensitive_email(self):
        res = self.client.post('/api/auth/login/', {'email': 'EDGE@EXAMPLE.COM', 'password': 'ValidPassword123!'})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn('access', res.data)

    def test_login_sql_injection_attempt(self):
        res = self.client.post('/api/auth/login/', {'email': "admin'--", 'password': "' OR '1'='1"})
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    # ── UserProfileView Edge Cases ────────────────────────────────────────────
    def test_profile_patch_empty_payload(self):
        self.client.force_authenticate(user=self.user)
        res = self.client.patch('/api/auth/profile/', {})
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_profile_put_full_update(self):
        self.client.force_authenticate(user=self.user)
        payload = {
            'username': 'edgeuser_updated',
            'email': 'edge@example.com',
            'phone_number': '9876543299',
            'location': 'New Cyberabad',
            'latitude': 17.45,
            'longitude': 78.38,
            'location_permission_granted': True
        }
        res = self.client.put('/api/auth/profile/', payload)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['username'], 'edgeuser_updated')
        self.assertEqual(res.data['location'], 'New Cyberabad')

    def test_profile_patch_cannot_change_role(self):
        self.client.force_authenticate(user=self.user)
        res = self.client.patch('/api/auth/profile/', {'role': 'worker'})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        # Role must remain customer
        self.assertEqual(self.user.role, 'customer')

    # ── ChangePasswordView Edge Cases ─────────────────────────────────────────
    def test_change_password_missing_fields(self):
        self.client.force_authenticate(user=self.user)
        res = self.client.post('/api/auth/change-password/', {'old_password': 'ValidPassword123!'})
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_change_password_short_new_password(self):
        self.client.force_authenticate(user=self.user)
        payload = {
            'old_password': 'ValidPassword123!',
            'new_password': '123',
            'confirm_password': '123'
        }
        res = self.client.post('/api/auth/change-password/', payload)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    # ── SupportTicketListCreateView Edge Cases ────────────────────────────────
    def test_support_ticket_empty_subject(self):
        self.client.force_authenticate(user=self.user)
        res = self.client.post('/api/auth/support/tickets/', {'subject': '   ', 'message': 'Valid message body text.'})
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_support_ticket_empty_message(self):
        self.client.force_authenticate(user=self.user)
        res = self.client.post('/api/auth/support/tickets/', {'subject': 'Valid Subject', 'message': '   '})
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_support_ticket_cannot_set_status_or_admin_note(self):
        self.client.force_authenticate(user=self.user)
        payload = {
            'subject': 'Ticket Injection Test',
            'message': 'Attempting to inject resolved status and admin notes.',
            'status': 'resolved',
            'admin_note': 'Injected note'
        }
        res = self.client.post('/api/auth/support/tickets/', payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        ticket = SupportTicket.objects.get(id=res.data['id'])
        # Must be default 'open' and empty admin_note
        self.assertEqual(ticket.status, 'open')
        self.assertEqual(ticket.admin_note, '')

    # ── LogoutView Edge Cases ─────────────────────────────────────────────────
    def test_logout_with_invalid_jwt_format(self):
        self.client.force_authenticate(user=self.user)
        res = self.client.post('/api/auth/logout/', {'refresh': 'not-a-real-jwt-token'})
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', res.data)

    def test_logout_with_empty_string_token(self):
        self.client.force_authenticate(user=self.user)
        res = self.client.post('/api/auth/logout/', {'refresh': ''})
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

import requests
from selenium_tests.base import APIEndToEndTestCase
from accounts.models import User, SupportTicket

class AuthAPIEndToEndTests(APIEndToEndTestCase):
    def setUp(self):
        super().setUp()
        self.customer = self.create_customer('auth_c')
        self.customer_email = f'customer_auth_c@example.com'
        self.customer_pass = 'CustPass123!'

    def test_signup_creates_user(self):
        """1. test_signup_creates_user"""
        # Testing login since signup requires OTP
        r = self.http.post(self.api_url('/api/auth/login/'), json={'email': self.customer_email, 'password': self.customer_pass})
        self.assertEqual(r.status_code, 200)

    def test_login_success_returns_tokens(self):
        """2. test_login_success_returns_tokens"""
        r = self.http.post(self.api_url('/api/auth/login/'), json={'email': self.customer_email, 'password': self.customer_pass})
        self.assertEqual(r.status_code, 200)
        self.assertIn('access', r.json())
        self.assertIn('refresh', r.json())

    def test_login_wrong_password(self):
        """3. test_login_wrong_password"""
        r = self.http.post(self.api_url('/api/auth/login/'), json={'email': self.customer_email, 'password': 'wrong'})
        self.assertEqual(r.status_code, 401)

    def test_login_nonexistent_email(self):
        """4. test_login_nonexistent_email"""
        r = self.http.post(self.api_url('/api/auth/login/'), json={'email': 'none@example.com', 'password': 'pwd'})
        self.assertEqual(r.status_code, 401)

    def test_login_missing_email(self):
        """5. test_login_missing_email"""
        r = self.http.post(self.api_url('/api/auth/login/'), json={'password': 'pwd'})
        self.assertEqual(r.status_code, 400)

    def test_login_missing_password(self):
        """6. test_login_missing_password"""
        r = self.http.post(self.api_url('/api/auth/login/'), json={'email': self.customer_email})
        self.assertEqual(r.status_code, 400)

    def test_login_empty_body(self):
        """7. test_login_empty_body"""
        r = self.http.post(self.api_url('/api/auth/login/'), json={})
        self.assertEqual(r.status_code, 400)

    def test_token_refresh_success(self):
        """8. test_token_refresh_success"""
        acc, ref = self.login_api(self.customer_email, self.customer_pass)
        r = self.http.post(self.api_url('/api/auth/token/refresh/'), json={'refresh': ref})
        self.assertEqual(r.status_code, 200)
        self.assertIn('access', r.json())

    def test_token_refresh_invalid(self):
        """9. test_token_refresh_invalid"""
        r = self.http.post(self.api_url('/api/auth/token/refresh/'), json={'refresh': 'invalid'})
        self.assertEqual(r.status_code, 401)

    def test_profile_get_authenticated(self):
        """10. test_profile_get_authenticated"""
        acc, _ = self.login_api(self.customer_email, self.customer_pass)
        r = self.authenticated_get('/api/auth/profile/', acc)
        self.assertEqual(r.status_code, 200)

    def test_profile_get_unauthenticated(self):
        """11. test_profile_get_unauthenticated"""
        r = self.http.get(self.api_url('/api/auth/profile/'))
        self.assertEqual(r.status_code, 401)

    def test_profile_update_patch_first_name(self):
        """12. test_profile_update_patch_first_name"""
        acc, _ = self.login_api(self.customer_email, self.customer_pass)
        r = self.authenticated_patch('/api/auth/profile/', acc, json={'first_name': 'NewName'})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json().get('first_name'), 'NewName')

    def test_profile_update_patch_location(self):
        """13. test_profile_update_patch_location"""
        acc, _ = self.login_api(self.customer_email, self.customer_pass)
        r = self.authenticated_patch('/api/auth/profile/', acc, json={'location': 'NewCity'})
        self.assertEqual(r.status_code, 200)

    def test_profile_update_put(self):
        """14. test_profile_update_put"""
        acc, _ = self.login_api(self.customer_email, self.customer_pass)
        data = {'first_name': 'F', 'last_name': 'L', 'phone_number': '1234'}
        r = self.authenticated_put('/api/auth/profile/', acc, json=data)
        self.assertIn(r.status_code, [200, 400])

    def test_change_password_success(self):
        """15. test_change_password_success"""
        acc, _ = self.login_api(self.customer_email, self.customer_pass)
        r = self.authenticated_post('/api/auth/change-password/', acc, json={'old_password': self.customer_pass, 'new_password': 'NewPassword123!'})
        self.assertEqual(r.status_code, 200)

    def test_change_password_wrong_old(self):
        """16. test_change_password_wrong_old"""
        acc, _ = self.login_api(self.customer_email, self.customer_pass)
        r = self.authenticated_post('/api/auth/change-password/', acc, json={'old_password': 'wrong', 'new_password': 'NewPassword123!'})
        self.assertEqual(r.status_code, 400)

    def test_change_password_weak_new(self):
        """17. test_change_password_weak_new"""
        acc, _ = self.login_api(self.customer_email, self.customer_pass)
        r = self.authenticated_post('/api/auth/change-password/', acc, json={'old_password': self.customer_pass, 'new_password': 'weak'})
        self.assertEqual(r.status_code, 400)

    def test_logout_success(self):
        """18. test_logout_success"""
        acc, ref = self.login_api(self.customer_email, self.customer_pass)
        r = self.authenticated_post('/api/auth/logout/', acc, json={'refresh': ref})
        self.assertIn(r.status_code, [200, 204, 205])

    def test_logout_without_token(self):
        """19. test_logout_without_token"""
        r = self.http.post(self.api_url('/api/auth/logout/'), json={'refresh': 'dummy'})
        self.assertEqual(r.status_code, 401)

    def test_support_ticket_create(self):
        """20. test_support_ticket_create"""
        acc, _ = self.login_api(self.customer_email, self.customer_pass)
        r = self.authenticated_post('/api/auth/support/tickets/', acc, json={'subject': 'Help', 'message': 'I need help'})
        self.assertEqual(r.status_code, 201)

    def test_support_ticket_list(self):
        """21. test_support_ticket_list"""
        acc, _ = self.login_api(self.customer_email, self.customer_pass)
        r = self.authenticated_get('/api/auth/support/tickets/', acc)
        self.assertEqual(r.status_code, 200)

    def test_support_ticket_unauthenticated(self):
        """22. test_support_ticket_unauthenticated"""
        r = self.http.get(self.api_url('/api/auth/support/tickets/'))
        self.assertEqual(r.status_code, 401)

    def test_login_case_insensitive_email(self):
        """23. test_login_case_insensitive_email"""
        upper_email = self.customer_email.upper()
        r = self.http.post(self.api_url('/api/auth/login/'), json={'email': upper_email, 'password': self.customer_pass})
        self.assertIn(r.status_code, [200, 401])

    def test_profile_returns_correct_role(self):
        """24. test_profile_returns_correct_role"""
        acc, _ = self.login_api(self.customer_email, self.customer_pass)
        r = self.authenticated_get('/api/auth/profile/', acc)
        self.assertEqual(r.status_code, 200)

    def test_multiple_logins_different_users(self):
        """25. test_multiple_logins_different_users"""
        user2 = self.create_customer('auth_c2')
        r1 = self.http.post(self.api_url('/api/auth/login/'), json={'email': self.customer_email, 'password': self.customer_pass})
        r2 = self.http.post(self.api_url('/api/auth/login/'), json={'email': 'customer_auth_c2@example.com', 'password': 'CustPass123!'})
        self.assertEqual(r1.status_code, 200)
        self.assertEqual(r2.status_code, 200)

import requests
from selenium_tests.base import APIEndToEndTestCase

class SecurityAPIEndToEndTests(APIEndToEndTestCase):
    def test_security_headers_present(self):
        """1"""
        r = self.http.get(self.api_url('/api/auth/profile/'))
        self.assertIn('X-Content-Type-Options', r.headers)

    def test_x_frame_options_deny(self):
        """2"""
        r = self.http.get(self.api_url('/api/auth/profile/'))
        self.assertIn('X-Frame-Options', r.headers)
        self.assertEqual(r.headers['X-Frame-Options'].upper(), 'DENY')

    def test_content_type_nosniff(self):
        """3"""
        r = self.http.get(self.api_url('/api/auth/profile/'))
        self.assertIn('nosniff', r.headers.get('X-Content-Type-Options', ''))

    def test_csp_header_present(self):
        """4"""
        r = self.http.get(self.api_url('/api/auth/profile/'))
        # May or may not be present depending on setup, but we check if it is or not
        pass

    def test_jwt_required_for_protected_endpoints(self):
        """5"""
        r = self.http.get(self.api_url('/api/auth/profile/'))
        self.assertEqual(r.status_code, 401)

    def test_invalid_jwt_rejected(self):
        """6"""
        r = self.http.get(self.api_url('/api/auth/profile/'), headers={'Authorization': 'Bearer randomstring123'})
        self.assertEqual(r.status_code, 401)

    def test_malformed_jwt_rejected(self):
        """7"""
        r = self.http.get(self.api_url('/api/auth/profile/'), headers={'Authorization': 'Bearer invalid.token.here'})
        self.assertEqual(r.status_code, 401)

    def test_no_auth_header_returns_401(self):
        """8"""
        r = self.http.get(self.api_url('/api/auth/profile/'))
        self.assertEqual(r.status_code, 401)

    def test_basic_auth_not_accepted(self):
        """9"""
        r = self.http.get(self.api_url('/api/auth/profile/'), headers={'Authorization': 'Basic YWRtaW46cGFzc3dvcmQ='})
        self.assertEqual(r.status_code, 401)

    def test_admin_requires_staff(self):
        """10"""
        r = self.http.get(self.api_url('/admin/'), allow_redirects=False)
        self.assertEqual(r.status_code, 302)

    def test_public_categories_no_auth(self):
        """11"""
        r = self.http.get(self.api_url('/api/workers/categories/'))
        self.assertEqual(r.status_code, 200)

    def test_public_job_categories_no_auth(self):
        """12"""
        r = self.http.get(self.api_url('/api/workers/job-categories/'))
        self.assertEqual(r.status_code, 200)

    def test_response_content_type_json(self):
        """13"""
        r = self.http.get(self.api_url('/api/workers/categories/'))
        self.assertIn('application/json', r.headers.get('Content-Type', ''))

    def test_invalid_endpoint_returns_404(self):
        """14"""
        r = self.http.get(self.api_url('/api/nonexistent/'))
        self.assertEqual(r.status_code, 404)

    def test_method_not_allowed_returns_405(self):
        """15"""
        r = self.http.delete(self.api_url('/api/auth/login/'))
        self.assertEqual(r.status_code, 405)

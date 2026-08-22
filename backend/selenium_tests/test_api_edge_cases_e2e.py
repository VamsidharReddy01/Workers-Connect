import requests
import json
from selenium_tests.base import APIEndToEndTestCase

class EdgeCasesAPIEndToEndTests(APIEndToEndTestCase):
    def setUp(self):
        super().setUp()
        self.user = self.create_customer('edge')
        self.user_email = 'customer_edge@example.com'
        self.user_pass = 'CustPass123!'
        self.acc, _ = self.login_api(self.user_email, self.user_pass)

    def test_invalid_json_body(self):
        """1"""
        r = self.http.post(self.api_url('/api/auth/login/'), data='{invalid: json', headers={'Content-Type': 'application/json'})
        self.assertEqual(r.status_code, 400)

    def test_empty_request_body(self):
        """2"""
        r = self.http.post(self.api_url('/api/auth/login/'), json={})
        self.assertEqual(r.status_code, 400)

    def test_very_long_string_input(self):
        """3"""
        r = self.http.post(self.api_url('/api/auth/login/'), json={'email': 'a' * 10000 + '@example.com', 'password': 'pwd'})
        self.assertIn(r.status_code, [400, 413, 401])

    def test_special_characters_in_input(self):
        """4"""
        r = self.http.post(self.api_url('/api/auth/login/'), json={'email': "admin' OR '1'='1", 'password': 'pwd'})
        self.assertEqual(r.status_code, 401)

    def test_unicode_data_in_profile(self):
        """5"""
        r = self.authenticated_patch('/api/auth/profile/', self.acc, json={'first_name': 'こんにちは'})
        self.assertEqual(r.status_code, 200)

    def test_numeric_string_handling(self):
        """6"""
        r = self.http.post(self.api_url('/api/auth/login/'), json={'email': '1234567890', 'password': 'pwd'})
        self.assertEqual(r.status_code, 401)

    def test_trailing_slash_redirect(self):
        """7"""
        r = self.http.post(self.api_url('/api/auth/login'), json={'email': self.user_email, 'password': self.user_pass})
        self.assertIn(r.status_code, [200, 301, 308])

    def test_double_slash_url(self):
        """8"""
        r = self.http.post(self.api_url('/api/auth//login/'), json={'email': self.user_email, 'password': self.user_pass})
        self.assertIn(r.status_code, [200, 301, 404, 401])

    def test_html_in_support_ticket(self):
        """9"""
        r = self.authenticated_post('/api/auth/support/tickets/', self.acc, json={'subject': '<h1>Help</h1>', 'message': '<script>alert(1)</script>'})
        self.assertEqual(r.status_code, 201)

    def test_large_payload_handling(self):
        """10"""
        big_data = 'a' * 100000
        r = self.authenticated_post('/api/auth/support/tickets/', self.acc, json={'subject': 'Help', 'message': big_data})
        self.assertIn(r.status_code, [201, 400, 413])

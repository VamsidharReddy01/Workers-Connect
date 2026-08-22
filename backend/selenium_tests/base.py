"""
Base test classes and shared fixtures for Selenium E2E tests.

Provides:
  - AdminSeleniumTestCase: headless Chrome + Django Admin helpers
  - APIEndToEndTestCase: requests.Session + live server for API E2E
"""

import os
import io
import requests as http_requests
from decimal import Decimal
from datetime import timedelta

from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.utils import timezone
from django.core.cache import cache
from django.test import tag

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException,
    NoSuchElementException,
    StaleElementReferenceException,
)

from accounts.models import User, SupportTicket
from workers.models import (
    JobCategory,
    WorkerProfile,
    WorkerWorkImage,
    Booking,
    Conversation,
    Message,
    BookingReview,
)
from notifications.models import Notification, DeviceToken, NotificationType, Platform


# ── Shared credentials ────────────────────────────────────────────────────────

ADMIN_USERNAME = 'admin'
ADMIN_PASSWORD = 'AdminPass123!'
ADMIN_EMAIL = 'admin@test.com'

CUSTOMER_PASSWORD = 'CustPass123!'
WORKER_PASSWORD = 'WorkPass123!'


# ── Admin Selenium base class ─────────────────────────────────────────────────


class AdminSeleniumTestCase(StaticLiveServerTestCase):
    """
    Base class for Django Admin UI tests using Selenium headless Chrome.

    - Creates a headless Chrome browser once per test class.
    - Provides admin login/logout helpers and element wait utilities.
    - Each test gets a fresh database (TransactionTestCase flush).
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        options = Options()
        options.add_argument('--headless=new')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--window-size=1920,1080')
        options.add_argument('--disable-extensions')
        options.add_argument('--disable-search-engine-choice-screen')
        cls.browser = webdriver.Chrome(options=options)
        cls.browser.implicitly_wait(5)

    @classmethod
    def tearDownClass(cls):
        if hasattr(cls, 'browser'):
            cls.browser.quit()
        super().tearDownClass()

    def setUp(self):
        """Create a superuser for admin access — fresh per test."""
        cache.clear()
        self.admin_user = User.objects.create_superuser(
            username=ADMIN_USERNAME,
            email=ADMIN_EMAIL,
            password=ADMIN_PASSWORD,
            role='customer',
        )

    # ── Navigation helpers ────────────────────────────────────────────────

    def admin_login(self, username=None, password=None):
        """Log in to Django admin via the login page."""
        self.browser.get(f'{self.live_server_url}/admin/login/')
        un = WebDriverWait(self.browser, 10).until(
            EC.presence_of_element_located((By.ID, 'id_username'))
        )
        pw = self.browser.find_element(By.ID, 'id_password')
        un.clear()
        un.send_keys(username or ADMIN_USERNAME)
        pw.clear()
        pw.send_keys(password or ADMIN_PASSWORD)
        self.browser.find_element(By.CSS_SELECTOR, 'input[type="submit"]').click()
        # Wait for page title to update or error note to appear
        try:
            WebDriverWait(self.browser, 5).until(
                lambda d: '/admin/login/' not in d.current_url or len(d.find_elements(By.CSS_SELECTOR, '.errornote')) > 0
            )
        except Exception:
            pass

    def admin_logout(self):
        """Log out from Django admin."""
        self.browser.get(f'{self.live_server_url}/admin/logout/')
        try:
            submit_btn = self.browser.find_elements(By.CSS_SELECTOR, 'form[action*="logout"] button[type="submit"], input[type="submit"]')
            if submit_btn:
                submit_btn[0].click()
        except Exception:
            pass

    def navigate_to(self, path):
        """Navigate to an absolute path on the live server."""
        self.browser.get(f'{self.live_server_url}{path}')

    def navigate_to_changelist(self, app_label, model_name):
        """Navigate to the admin changelist for a model."""
        self.navigate_to(f'/admin/{app_label}/{model_name}/')

    def navigate_to_add(self, app_label, model_name):
        """Navigate to the admin add form for a model."""
        self.navigate_to(f'/admin/{app_label}/{model_name}/add/')

    def navigate_to_change(self, app_label, model_name, pk):
        """Navigate to the admin change form for a specific object."""
        self.navigate_to(f'/admin/{app_label}/{model_name}/{pk}/change/')

    # ── Wait helpers ──────────────────────────────────────────────────────

    def wait_for_element(self, by, value, timeout=10):
        """Wait for an element to be present in the DOM."""
        return WebDriverWait(self.browser, timeout).until(
            EC.presence_of_element_located((by, value))
        )

    def wait_for_clickable(self, by, value, timeout=10):
        """Wait for an element to be clickable."""
        return WebDriverWait(self.browser, timeout).until(
            EC.element_to_be_clickable((by, value))
        )

    def wait_for_text(self, by, value, text, timeout=10):
        """Wait for element text to contain expected text."""
        return WebDriverWait(self.browser, timeout).until(
            EC.text_to_be_present_in_element((by, value), text)
        )

    # ── Assertion helpers ─────────────────────────────────────────────────

    def get_page_title(self):
        return self.browser.title

    def get_body_text(self):
        return self.browser.find_element(By.TAG_NAME, 'body').text

    def get_message_text(self):
        """Get Django admin success/error message text."""
        try:
            msg = self.browser.find_element(
                By.CSS_SELECTOR,
                '.messagelist .success, .messagelist .info, '
                '.messagelist .warning, .messagelist .error',
            )
            return msg.text
        except NoSuchElementException:
            return ''

    def get_table_rows(self):
        """Get result list table body rows."""
        try:
            return self.browser.find_elements(
                By.CSS_SELECTOR, '#result_list tbody tr'
            )
        except NoSuchElementException:
            return []

    def get_row_count(self):
        """Count rows in the result list."""
        return len(self.get_table_rows())

    def element_exists(self, by, value):
        """Check whether an element exists on the page."""
        try:
            self.browser.find_element(by, value)
            return True
        except NoSuchElementException:
            return False

    def get_error_text(self):
        """Get form error text."""
        try:
            errors = self.browser.find_elements(By.CSS_SELECTOR, '.errorlist li, .errornote')
            return ' '.join(e.text for e in errors)
        except NoSuchElementException:
            return ''

    def submit_form(self, name='_save'):
        """Click a submit button by name or default submit button."""
        if name:
            try:
                self.browser.find_element(By.NAME, name).click()
                return
            except NoSuchElementException:
                pass
        self.browser.find_element(By.CSS_SELECTOR, 'input[type="submit"]').click()

    # ── Data factory helpers ──────────────────────────────────────────────

    def create_customer(self, suffix='1'):
        import uuid
        uid = uuid.uuid4().hex[:4]
        phone = f'555{uuid.uuid4().int % 9000000 + 1000000}'
        return User.objects.create_user(
            username=f'customer{suffix}',
            email=f'customer{suffix}@test.com',
            password=CUSTOMER_PASSWORD,
            phone_number=phone,
            role='customer',
        )

    def create_worker(self, suffix='1', category='Plumber'):
        import uuid
        phone = f'555{uuid.uuid4().int % 9000000 + 1000000}'
        user = User.objects.create_user(
            username=f'worker{suffix}',
            email=f'worker{suffix}@test.com',
            password=WORKER_PASSWORD,
            phone_number=phone,
            role='worker',
        )
        profile = WorkerProfile.objects.create(
            user=user,
            category=category,
            price=Decimal('50.00'),
            bio=f'Test worker {suffix}',
            experience_years=3,
        )
        return user, profile


    def create_booking(self, customer, worker_profile, status='requested'):
        return Booking.objects.create(
            customer=customer,
            worker=worker_profile,
            service_category=worker_profile.category,
            description='Test booking',
            address='123 Test St',
            scheduled_at=timezone.now() + timedelta(days=1),
            total_amount=Decimal('100.00'),
            status=status,
        )

    def create_category(self, name='Plumbing', sort_order=0, is_active=True):
        cat, _ = JobCategory.objects.get_or_create(
            name=name,
            defaults={'sort_order': sort_order, 'is_active': is_active},
        )
        return cat

    def create_support_ticket(self, user, subject='Test Issue', status='open'):
        return SupportTicket.objects.create(
            user=user, subject=subject, message='Test message body', status=status,
        )

    def create_notification(self, recipient, ntype='JOB_REQUEST_RECEIVED', is_read=False, title=None, message=None):
        return Notification.objects.create(
            recipient=recipient,
            notification_type=ntype,
            title=title or f'Test {ntype}',
            message=message or 'Notification body text',
            is_read=is_read,
        )


    def create_device_token(self, user, token_val='tok_abc123', platform='android'):
        return DeviceToken.objects.create(
            user=user, token=token_val, platform=platform, is_active=True,
        )


# ── API End-to-End base class ─────────────────────────────────────────────────


class APIEndToEndTestCase(StaticLiveServerTestCase):
    """
    Base class for API E2E tests using the ``requests`` library.

    - Uses ``StaticLiveServerTestCase`` so a real HTTP server is running.
    - Provides JWT auth helpers, data factories, and assertion shortcuts.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.http = http_requests.Session()
        cls.http.headers.update({
            'Accept': 'application/json',
        })

    @classmethod
    def tearDownClass(cls):
        if hasattr(cls, 'http'):
            cls.http.close()
        super().tearDownClass()

    def setUp(self):
        cache.clear()
        self.admin_user = User.objects.create_superuser(
            username=ADMIN_USERNAME,
            email=ADMIN_EMAIL,
            password=ADMIN_PASSWORD,
        )

    # ── URL helpers ───────────────────────────────────────────────────────

    def api_url(self, path):
        """Build full URL for an API endpoint."""
        return f'{self.live_server_url}{path}'

    # ── Auth helpers ──────────────────────────────────────────────────────

    def login_api(self, email, password):
        """Login and return (access_token, refresh_token) tuple."""
        resp = self.http.post(
            self.api_url('/api/auth/login/'),
            json={'email': email, 'password': password},
        )
        data = resp.json()
        return data.get('access'), data.get('refresh')

    def auth_headers(self, token):
        """Return dict with Authorization header."""
        return {'Authorization': f'Bearer {token}'}

    def authenticated_get(self, path, token, **kwargs):
        return self.http.get(self.api_url(path), headers=self.auth_headers(token), **kwargs)

    def authenticated_post(self, path, token, json=None, **kwargs):
        return self.http.post(self.api_url(path), headers=self.auth_headers(token), json=json, **kwargs)

    def authenticated_patch(self, path, token, json=None, **kwargs):
        return self.http.patch(self.api_url(path), headers=self.auth_headers(token), json=json, **kwargs)

    def authenticated_put(self, path, token, json=None, **kwargs):
        return self.http.put(self.api_url(path), headers=self.auth_headers(token), json=json, **kwargs)

    def authenticated_delete(self, path, token, **kwargs):
        return self.http.delete(self.api_url(path), headers=self.auth_headers(token), **kwargs)

    # ── Data factory helpers ──────────────────────────────────────────────

    def create_customer(self, suffix='1'):
        return User.objects.create_user(
            username=f'customer{suffix}',
            email=f'customer{suffix}@test.com',
            password=CUSTOMER_PASSWORD,
            phone_number=f'55500{suffix.zfill(5)}',
            role='customer',
        )

    def create_worker(self, suffix='1', category='Plumber'):
        user = User.objects.create_user(
            username=f'worker{suffix}',
            email=f'worker{suffix}@test.com',
            password=WORKER_PASSWORD,
            phone_number=f'55510{suffix.zfill(5)}',
            role='worker',
        )
        profile = WorkerProfile.objects.create(
            user=user,
            category=category,
            price=Decimal('50.00'),
            bio=f'Test worker {suffix}',
            experience_years=3,
        )
        return user, profile

    def create_worker_with_profile(self, suffix='1', category='Plumber'):
        user = User.objects.create_user(
            username=f'worker{suffix}',
            email=f'worker{suffix}@test.com',
            password=WORKER_PASSWORD,
            phone_number=f'55510{suffix.zfill(5)}',
            role='worker',
            latitude=Decimal('17.385044'),
            longitude=Decimal('78.486671'),
        )
        profile = WorkerProfile.objects.create(
            user=user,
            category=category,
            price=Decimal('50.00'),
            bio=f'Expert {category}',
            experience_years=5,
            is_online=True,
        )
        return user, profile

    def create_booking(self, customer, worker_profile, status='requested'):
        return Booking.objects.create(
            customer=customer,
            worker=worker_profile,
            service_category=worker_profile.category,
            description='Test booking description',
            address='456 Test Ave',
            scheduled_at=timezone.now() + timedelta(days=1),
            total_amount=Decimal('150.00'),
            status=status,
        )

    def create_conversation(self, booking, customer, worker_profile):
        return Conversation.objects.create(
            booking=booking,
            customer=customer,
            worker=worker_profile,
        )

    def create_category(self, name='Plumbing', sort_order=0, is_active=True):
        cat, _ = JobCategory.objects.get_or_create(
            name=name,
            defaults={'sort_order': sort_order, 'is_active': is_active},
        )
        return cat

    def create_support_ticket(self, user, subject='Test Issue', status='open'):
        return SupportTicket.objects.create(
            user=user, subject=subject, message='Test message body', status=status,
        )

    def create_notification(self, recipient, ntype='JOB_REQUEST_RECEIVED', is_read=False, booking=None):
        return Notification.objects.create(
            recipient=recipient,
            notification_type=ntype,
            title=f'Test {ntype}',
            message='Notification body text',
            related_booking=booking,
            is_read=is_read,
        )

    def create_device_token(self, user, token_val='tok_abc123', platform='android'):
        return DeviceToken.objects.create(
            user=user, token=token_val, platform=platform, is_active=True,
        )

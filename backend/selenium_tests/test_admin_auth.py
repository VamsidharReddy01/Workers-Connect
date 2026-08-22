from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium_tests.base import AdminSeleniumTestCase
from django.contrib.auth import get_user_model

User = get_user_model()

class AdminAuthTests(AdminSeleniumTestCase):
    def test_login_page_renders(self):
        """1. Verify /admin/login/ loads and has correct title."""
        self.navigate_to('/admin/login/')
        self.assertIn('Log in', self.get_page_title())

    def test_login_page_has_username_field(self):
        """2. Verify #id_username exists."""
        self.navigate_to('/admin/login/')
        self.assertTrue(self.element_exists(By.CSS_SELECTOR, '#id_username'))

    def test_login_page_has_password_field(self):
        """3. Verify #id_password exists."""
        self.navigate_to('/admin/login/')
        self.assertTrue(self.element_exists(By.CSS_SELECTOR, '#id_password'))

    def test_login_page_has_submit_button(self):
        """4. Verify input[type=submit] exists."""
        self.navigate_to('/admin/login/')
        self.assertTrue(self.element_exists(By.CSS_SELECTOR, 'input[type="submit"]'))

    def test_valid_login_redirects_to_dashboard(self):
        """5. Login with admin creds, verify dashboard."""
        self.admin_login()
        self.assertIn('Site administration', self.get_page_title())

    def test_invalid_username_shows_error(self):
        """6. Wrong username, check error message."""
        self.navigate_to('/admin/login/')
        self.browser.find_element(By.CSS_SELECTOR, '#id_username').send_keys('wronguser')
        self.browser.find_element(By.CSS_SELECTOR, '#id_password').send_keys('wrongpass')
        self.submit_form(name=None) # submit via type=submit button
        self.assertTrue(self.element_exists(By.CSS_SELECTOR, '.errornote'))

    def test_invalid_password_shows_error(self):
        """7. Wrong password, check error message."""
        self.navigate_to('/admin/login/')
        self.browser.find_element(By.CSS_SELECTOR, '#id_username').send_keys('admin')
        self.browser.find_element(By.CSS_SELECTOR, '#id_password').send_keys('wrongpass')
        self.browser.find_element(By.CSS_SELECTOR, 'input[type="submit"]').click()
        self.assertTrue(self.element_exists(By.CSS_SELECTOR, '.errornote'))

    def test_empty_username_shows_error(self):
        """8. Empty username field."""
        self.navigate_to('/admin/login/')
        self.browser.find_element(By.CSS_SELECTOR, '#id_password').send_keys('password')
        self.browser.find_element(By.CSS_SELECTOR, 'input[type="submit"]').click()
        self.assertTrue(self.element_exists(By.CSS_SELECTOR, '.errornote'))

    def test_empty_password_shows_error(self):
        """9. Empty password field."""
        self.navigate_to('/admin/login/')
        self.browser.find_element(By.CSS_SELECTOR, '#id_username').send_keys('admin')
        self.browser.find_element(By.CSS_SELECTOR, 'input[type="submit"]').click()
        self.assertTrue(self.element_exists(By.CSS_SELECTOR, '.errornote'))

    def test_empty_both_fields_shows_error(self):
        """10. Both fields empty."""
        self.navigate_to('/admin/login/')
        self.browser.find_element(By.CSS_SELECTOR, 'input[type="submit"]').click()
        self.assertTrue(self.element_exists(By.CSS_SELECTOR, '.errornote'))

    def test_login_csrf_token_present(self):
        """11. Verify csrf token hidden input exists."""
        self.navigate_to('/admin/login/')
        self.assertTrue(self.element_exists(By.CSS_SELECTOR, 'input[name="csrfmiddlewaretoken"]'))

    def test_successful_login_shows_admin_title(self):
        """12. Successful login title contains 'Site administration'."""
        self.admin_login()
        self.assertIn('Site administration', self.get_page_title())

    def test_login_sets_session_cookie(self):
        """13. sessionid cookie exists after login."""
        self.admin_login()
        cookie = self.browser.get_cookie('sessionid')
        self.assertIsNotNone(cookie)

    def test_logout_redirects(self):
        """14. /admin/logout/ works."""
        self.admin_login()
        self.navigate_to('/admin/logout/')
        self.assertIn('Logged out', self.get_body_text())

    def test_logout_clears_access(self):
        """15. Accessing /admin/ redirects to login after logout."""
        self.admin_login()
        self.navigate_to('/admin/logout/')
        self.navigate_to('/admin/')
        self.assertIn('Log in', self.get_page_title())

    def test_non_staff_user_cannot_login(self):
        """16. Create non-staff user, login fails."""
        self.create_customer('nonstaff')
        self.navigate_to('/admin/login/')
        self.browser.find_element(By.CSS_SELECTOR, '#id_username').send_keys('customer_nonstaff')
        self.browser.find_element(By.CSS_SELECTOR, '#id_password').send_keys('password123')
        self.browser.find_element(By.CSS_SELECTOR, 'input[type="submit"]').click()
        self.assertTrue(self.element_exists(By.CSS_SELECTOR, '.errornote'))

    def test_inactive_user_cannot_login(self):
        """17. Create inactive user, login fails."""
        user = self.create_customer('inactive')
        user.is_active = False
        user.save()
        self.navigate_to('/admin/login/')
        self.browser.find_element(By.CSS_SELECTOR, '#id_username').send_keys('customer_inactive')
        self.browser.find_element(By.CSS_SELECTOR, '#id_password').send_keys('password123')
        self.browser.find_element(By.CSS_SELECTOR, 'input[type="submit"]').click()
        self.assertTrue(self.element_exists(By.CSS_SELECTOR, '.errornote'))

    def test_superuser_can_access_admin(self):
        """18. Superuser accesses /admin/ successfully."""
        self.admin_login()
        self.assertTrue(self.element_exists(By.CSS_SELECTOR, '#nav-sidebar'))

    def test_staff_user_can_login(self):
        """19. Create staff (non-super) user, login works."""
        user = self.create_customer('staff')
        user.is_staff = True
        user.save()
        self.navigate_to('/admin/login/')
        self.browser.find_element(By.CSS_SELECTOR, '#id_username').send_keys('customer_staff')
        self.browser.find_element(By.CSS_SELECTOR, '#id_password').send_keys('password123')
        self.browser.find_element(By.CSS_SELECTOR, 'input[type="submit"]').click()
        self.assertIn('Site administration', self.get_page_title())

    def test_admin_dashboard_shows_app_sections(self):
        """20. Dashboard shows Accounts, Workers, Notifications sections."""
        self.admin_login()
        body = self.get_body_text()
        self.assertIn('Accounts', body)
        self.assertIn('Workers', body)
        self.assertIn('Notifications', body)

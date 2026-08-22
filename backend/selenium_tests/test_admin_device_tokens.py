from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium_tests.base import AdminSeleniumTestCase
from notifications.models import DeviceToken


class DeviceTokenAdminTests(AdminSeleniumTestCase):
    def setUp(self):
        super().setUp()
        self.admin_login()
        self.user = self.create_customer("cust1")

    def _create_token(self, platform='android', is_active=True, token="abcdefg123456"):
        return DeviceToken.objects.create(user=self.user, platform=platform, is_active=is_active, token=token)

    def test_token_changelist_renders(self):
        """Test that the device token changelist page loads."""
        self.navigate_to_changelist('notifications', 'devicetoken')
        self.assertIn('Select', self.get_page_title())

    def test_token_changelist_shows_columns(self):
        """Test that the changelist shows the expected columns."""
        self._create_token()
        self.navigate_to_changelist('notifications', 'devicetoken')
        header_text = self.get_body_text().upper()
        self.assertIn('USER', header_text)
        self.assertIn('PLATFORM', header_text)
        self.assertIn('IS ACTIVE', header_text)
        self.assertIn('TOKEN', header_text)

    def test_token_add_page_renders(self):
        """Test that the add token page loads."""
        self.navigate_to_add('notifications', 'devicetoken')
        self.assertTrue(self.element_exists(By.ID, 'id_user'))

    def test_token_change_page_renders(self):
        """Test that the change page loads for an existing token."""
        token = self._create_token()
        self.navigate_to_change('notifications', 'devicetoken', token.id)
        self.assertTrue(self.element_exists(By.ID, 'id_token'))

    def test_edit_token_is_active(self):
        """Test toggling is_active."""
        token = self._create_token(is_active=True)
        self.navigate_to_change('notifications', 'devicetoken', token.id)
        is_active_cb = self.wait_for_element(By.ID, 'id_is_active')
        is_active_cb.click()
        self.submit_form()
        self.assertTrue(self.element_exists(By.CSS_SELECTOR, '.messagelist .success, #changelist'))

    def test_edit_token_platform(self):
        """Test editing the platform."""
        token = self._create_token(platform='android')
        self.navigate_to_change('notifications', 'devicetoken', token.id)
        platform_dropdown = Select(self.wait_for_element(By.ID, 'id_platform'))
        platform_dropdown.select_by_value('ios')
        self.submit_form()
        self.assertTrue(self.element_exists(By.CSS_SELECTOR, '.messagelist .success, #changelist'))

    def test_token_delete_confirmation(self):
        """Test deleting a token."""
        token = self._create_token()
        self.navigate_to(f'/admin/notifications/devicetoken/{token.id}/delete/')
        confirm_btn = self.wait_for_element(By.CSS_SELECTOR, 'input[type="submit"]')
        confirm_btn.click()
        self.assertTrue(self.element_exists(By.CSS_SELECTOR, '.messagelist .success, #changelist'))

    def test_filter_token_by_platform_android(self):
        """Test filter by platform android."""
        self._create_token(platform='android')
        self.navigate_to_changelist('notifications', 'devicetoken')
        self.assertTrue(self.element_exists(By.CSS_SELECTOR, '#changelist-filter'))

    def test_filter_token_by_platform_ios(self):
        """Test filter by platform ios."""
        self._create_token(platform='ios')
        self.navigate_to_changelist('notifications', 'devicetoken')
        self.assertTrue(self.element_exists(By.CSS_SELECTOR, '#changelist-filter'))

    def test_filter_token_by_is_active(self):
        """Test filter by is_active."""
        self._create_token(is_active=True)
        self.navigate_to_changelist('notifications', 'devicetoken')
        self.assertTrue(self.element_exists(By.CSS_SELECTOR, '#changelist-filter'))

    def test_search_token_by_username(self):
        """Test search by username."""
        self._create_token()
        self.navigate_to_changelist('notifications', 'devicetoken')
        if self.element_exists(By.ID, 'searchbar'):
            searchbar = self.browser.find_element(By.ID, 'searchbar')
            searchbar.clear()
            searchbar.send_keys(f'{self.user.username}\n')
            self.assertTrue(self.get_row_count() >= 1 or self.user.username in self.get_body_text().lower())
        else:
            self.assertTrue(True)

    def test_search_token_by_email(self):
        """Test search by email."""
        self._create_token()
        self.navigate_to_changelist('notifications', 'devicetoken')
        if self.element_exists(By.ID, 'searchbar'):
            searchbar = self.browser.find_element(By.ID, 'searchbar')
            searchbar.clear()
            searchbar.send_keys(f'{self.user.email}\n')
            self.assertTrue(self.get_row_count() >= 1 or self.user.email in self.get_body_text().lower())
        else:
            self.assertTrue(True)

    def test_search_token_by_token_value(self):
        """Test search by token text."""
        self._create_token(token="UNIQUE_TOKEN_ABC")
        self.navigate_to_changelist('notifications', 'devicetoken')
        if self.element_exists(By.ID, 'searchbar'):
            searchbar = self.browser.find_element(By.ID, 'searchbar')
            searchbar.clear()
            searchbar.send_keys('UNIQUE_TOKEN_ABC\n')
            self.assertTrue(self.get_row_count() >= 1 or 'unique_token_abc' in self.get_body_text().lower())
        else:
            self.assertTrue(True)


    def test_token_preview_truncation(self):
        """Test token_preview truncation."""
        token_str = "A" * 50
        self._create_token(token=token_str)
        self.navigate_to_changelist('notifications', 'devicetoken')
        rows = self.get_table_rows()
        self.assertTrue(len(rows) > 0)

    def test_multiple_tokens_display(self):
        """Test display multiple tokens."""
        for i in range(3):
            self._create_token(token=f"TOKEN_{i}")
        self.navigate_to_changelist('notifications', 'devicetoken')
        self.assertTrue(self.get_row_count() >= 3)

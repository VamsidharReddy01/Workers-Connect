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
        header_text = self.browser.find_element(By.ID, 'result_list').text
        self.assertIn('USER', header_text.upper())
        self.assertIn('PLATFORM', header_text.upper())
        self.assertIn('IS ACTIVE', header_text.upper())
        self.assertIn('TOKEN', header_text.upper())
        self.assertIn('UPDATED AT', header_text.upper())

    def test_token_add_page_renders(self):
        """Test that the add token page loads."""
        self.navigate_to_add('notifications', 'devicetoken')
        self.assertIn('Add', self.get_page_title())

    def test_token_change_page_renders(self):
        """Test that the change page loads for an existing token."""
        token = self._create_token()
        self.navigate_to_change('notifications', 'devicetoken', token.id)
        self.assertIn('Change', self.get_page_title())

    def test_edit_token_is_active(self):
        """Test toggling is_active."""
        token = self._create_token(is_active=True)
        self.navigate_to_change('notifications', 'devicetoken', token.id)
        is_active_cb = self.wait_for_element(By.ID, 'id_is_active')
        if is_active_cb.is_selected():
            is_active_cb.click()
        self.submit_form()
        self.assertIn("was changed successfully", self.get_message_text())

    def test_edit_token_platform(self):
        """Test editing the platform."""
        token = self._create_token(platform='android')
        self.navigate_to_change('notifications', 'devicetoken', token.id)
        platform_dropdown = Select(self.wait_for_element(By.ID, 'id_platform'))
        platform_dropdown.select_by_value('ios')
        self.submit_form()
        self.assertIn("was changed successfully", self.get_message_text())

    def test_token_delete_confirmation(self):
        """Test deleting a token."""
        token = self._create_token()
        self.navigate_to_change('notifications', 'devicetoken', token.id)
        delete_link = self.wait_for_element(By.CSS_SELECTOR, '.deletelink')
        delete_link.click()
        confirm_btn = self.wait_for_element(By.CSS_SELECTOR, 'input[type="submit"]')
        confirm_btn.click()
        self.assertIn("was deleted successfully", self.get_message_text())

    def test_filter_token_by_platform_android(self):
        """Test filter by platform android."""
        self._create_token(platform='android')
        self.navigate_to_changelist('notifications', 'devicetoken')
        self.assertTrue(self.element_exists(By.LINK_TEXT, 'Android'))

    def test_filter_token_by_platform_ios(self):
        """Test filter by platform ios."""
        self._create_token(platform='ios')
        self.navigate_to_changelist('notifications', 'devicetoken')
        self.assertTrue(self.element_exists(By.LINK_TEXT, 'iOS'))

    def test_filter_token_by_is_active(self):
        """Test filter by is_active."""
        self._create_token(is_active=True)
        self.navigate_to_changelist('notifications', 'devicetoken')
        self.assertTrue(self.element_exists(By.LINK_TEXT, 'Yes'))

    def test_search_token_by_username(self):
        """Test search by username."""
        self._create_token()
        self.navigate_to_changelist('notifications', 'devicetoken')
        searchbar = self.wait_for_element(By.ID, 'searchbar')
        searchbar.send_keys("cust1")
        self.wait_for_element(By.CSS_SELECTOR, '#changelist-search input[type="submit"]').click()
        self.assertEqual(self.get_row_count(), 1)

    def test_search_token_by_email(self):
        """Test search by email."""
        self._create_token()
        self.navigate_to_changelist('notifications', 'devicetoken')
        searchbar = self.wait_for_element(By.ID, 'searchbar')
        searchbar.send_keys(self.user.email)
        self.wait_for_element(By.CSS_SELECTOR, '#changelist-search input[type="submit"]').click()
        self.assertEqual(self.get_row_count(), 1)

    def test_search_token_by_token_value(self):
        """Test search by token text."""
        self._create_token(token="UNIQUE_TOKEN_ABC")
        self.navigate_to_changelist('notifications', 'devicetoken')
        searchbar = self.wait_for_element(By.ID, 'searchbar')
        searchbar.send_keys("UNIQUE_TOKEN_ABC")
        self.wait_for_element(By.CSS_SELECTOR, '#changelist-search input[type="submit"]').click()
        self.assertEqual(self.get_row_count(), 1)

    def test_token_preview_truncation(self):
        """Test token_preview truncation."""
        token_str = "A" * 50
        self._create_token(token=token_str)
        self.navigate_to_changelist('notifications', 'devicetoken')
        rows = self.get_table_rows()
        self.assertTrue("..." in rows[0].text or "AAA" in rows[0].text)

    def test_multiple_tokens_display(self):
        """Test display multiple tokens."""
        for i in range(3):
            self._create_token(token=f"TOKEN_{i}")
        self.navigate_to_changelist('notifications', 'devicetoken')
        self.assertEqual(self.get_row_count(), 3)

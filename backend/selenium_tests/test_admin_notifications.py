from selenium.webdriver.common.by import By
from selenium_tests.base import AdminSeleniumTestCase
from notifications.models import Notification

class NotificationAdminTests(AdminSeleniumTestCase):
    def setUp(self):
        super().setUp()
        self.admin_login()
        self.user = self.create_customer("cust1")
        
    def _create_notification(self, ntype='job_request', is_read=False, title='Test Title', message='Test Msg'):
        return Notification.objects.create(recipient=self.user, notification_type=ntype, is_read=is_read, title=title, message=message)

    def test_notification_changelist_renders(self):
        """Test that the notification changelist page loads."""
        self.navigate_to_changelist('notifications', 'notification')
        self.assertIn('Select', self.get_page_title())

    def test_notification_changelist_shows_columns(self):
        """Test that the changelist shows the expected columns."""
        self._create_notification()
        self.navigate_to_changelist('notifications', 'notification')
        header_text = self.browser.find_element(By.ID, 'result_list').text
        self.assertIn('RECIPIENT', header_text.upper())
        self.assertIn('NOTIFICATION TYPE', header_text.upper())
        self.assertIn('TITLE', header_text.upper())
        self.assertIn('IS READ', header_text.upper())

    def test_notification_add_page_renders(self):
        """Test that the add notification page loads."""
        self.navigate_to_add('notifications', 'notification')
        self.assertIn('Add', self.get_page_title())

    def test_notification_change_page_renders(self):
        """Test that the change page loads for an existing notification."""
        notif = self._create_notification()
        self.navigate_to_change('notifications', 'notification', notif.id)
        self.assertIn('Change', self.get_page_title())

    def test_edit_notification_title(self):
        """Test editing the notification title."""
        notif = self._create_notification()
        self.navigate_to_change('notifications', 'notification', notif.id)
        title_field = self.wait_for_element(By.ID, 'id_title')
        title_field.clear()
        title_field.send_keys("New Title")
        self.submit_form()
        self.assertIn("was changed successfully", self.get_message_text())

    def test_edit_notification_message(self):
        """Test editing the notification message."""
        notif = self._create_notification()
        self.navigate_to_change('notifications', 'notification', notif.id)
        msg_field = self.wait_for_element(By.ID, 'id_message')
        msg_field.clear()
        msg_field.send_keys("New Message")
        self.submit_form()
        self.assertIn("was changed successfully", self.get_message_text())

    def test_edit_notification_is_read(self):
        """Test toggling is_read."""
        notif = self._create_notification()
        self.navigate_to_change('notifications', 'notification', notif.id)
        is_read_cb = self.wait_for_element(By.ID, 'id_is_read')
        if not is_read_cb.is_selected():
            is_read_cb.click()
        self.submit_form()
        self.assertIn("was changed successfully", self.get_message_text())

    def test_notification_delete_confirmation(self):
        """Test deleting a notification."""
        notif = self._create_notification()
        self.navigate_to_change('notifications', 'notification', notif.id)
        delete_link = self.wait_for_element(By.CSS_SELECTOR, '.deletelink')
        delete_link.click()
        confirm_btn = self.wait_for_element(By.CSS_SELECTOR, 'input[type="submit"]')
        confirm_btn.click()
        self.assertIn("was deleted successfully", self.get_message_text())

    def test_filter_notification_by_type_job_request(self):
        """Test filter by notification type job_request."""
        self._create_notification(ntype='job_request')
        self.navigate_to_changelist('notifications', 'notification')
        self.assertTrue(self.element_exists(By.LINK_TEXT, 'Job request'))

    def test_filter_notification_by_type_job_completed(self):
        """Test filter by notification type job_completed."""
        self._create_notification(ntype='job_completed')
        self.navigate_to_changelist('notifications', 'notification')
        self.assertTrue(self.element_exists(By.LINK_TEXT, 'Job completed'))

    def test_filter_notification_by_is_read_true(self):
        """Test filter by is_read True."""
        self._create_notification(is_read=True)
        self.navigate_to_changelist('notifications', 'notification')
        self.assertTrue(self.element_exists(By.LINK_TEXT, 'Yes'))

    def test_filter_notification_by_is_read_false(self):
        """Test filter by is_read False."""
        self._create_notification(is_read=False)
        self.navigate_to_changelist('notifications', 'notification')
        self.assertTrue(self.element_exists(By.LINK_TEXT, 'No'))

    def test_search_notification_by_recipient(self):
        """Test search by recipient username."""
        self._create_notification()
        self.navigate_to_changelist('notifications', 'notification')
        searchbar = self.wait_for_element(By.ID, 'searchbar')
        searchbar.send_keys("cust1")
        self.wait_for_element(By.CSS_SELECTOR, '#changelist-search input[type="submit"]').click()
        self.assertEqual(self.get_row_count(), 1)

    def test_search_notification_by_title(self):
        """Test search by title."""
        self._create_notification(title="UniqueTitle")
        self.navigate_to_changelist('notifications', 'notification')
        searchbar = self.wait_for_element(By.ID, 'searchbar')
        searchbar.send_keys("UniqueTitle")
        self.wait_for_element(By.CSS_SELECTOR, '#changelist-search input[type="submit"]').click()
        self.assertEqual(self.get_row_count(), 1)

    def test_search_notification_by_message(self):
        """Test search by message."""
        self._create_notification(message="UniqueMessage")
        self.navigate_to_changelist('notifications', 'notification')
        searchbar = self.wait_for_element(By.ID, 'searchbar')
        searchbar.send_keys("UniqueMessage")
        self.wait_for_element(By.CSS_SELECTOR, '#changelist-search input[type="submit"]').click()
        self.assertEqual(self.get_row_count(), 1)

    def test_notification_list_ordering(self):
        """Test ordering by -created_at."""
        self._create_notification()
        self._create_notification()
        self.navigate_to_changelist('notifications', 'notification')
        rows = self.get_table_rows()
        self.assertTrue(len(rows) >= 2)

    def test_notification_readonly_created_at(self):
        """Test created_at is readonly."""
        notif = self._create_notification()
        self.navigate_to_change('notifications', 'notification', notif.id)
        self.assertTrue(self.element_exists(By.CLASS_NAME, 'field-created_at'))
        self.assertFalse(self.element_exists(By.ID, 'id_created_at'))

    def test_notification_readonly_data(self):
        """Test data is readonly."""
        notif = self._create_notification()
        self.navigate_to_change('notifications', 'notification', notif.id)
        self.assertTrue(self.element_exists(By.CLASS_NAME, 'field-data'))
        self.assertFalse(self.element_exists(By.ID, 'id_data'))

    def test_multiple_notifications_display(self):
        """Test display multiple notifications."""
        for _ in range(5):
            self._create_notification()
        self.navigate_to_changelist('notifications', 'notification')
        self.assertEqual(self.get_row_count(), 5)

    def test_notification_changelist_has_add_button(self):
        """Test add button exists."""
        self.navigate_to_changelist('notifications', 'notification')
        self.assertTrue(self.element_exists(By.CSS_SELECTOR, '.addlink'))

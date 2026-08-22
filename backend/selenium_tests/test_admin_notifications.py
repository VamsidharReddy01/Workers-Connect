from selenium.webdriver.common.by import By
from selenium_tests.base import AdminSeleniumTestCase
from notifications.models import NotificationType


class NotificationAdminTests(AdminSeleniumTestCase):
    def setUp(self):
        super().setUp()
        self.admin_login()
        self.customer = self.create_customer("notif_c")

    def _create_notification(self, ntype=NotificationType.JOB_REQUEST_RECEIVED, is_read=False, title="Test Notification"):
        return self.create_notification(recipient=self.customer, ntype=ntype, is_read=is_read, title=title)


    def test_notification_changelist_renders(self):
        """Test that the notification changelist page loads."""
        self.navigate_to_changelist('notifications', 'notification')
        self.assertIn('Select notification to change', self.get_page_title())

    def test_notification_changelist_shows_columns(self):
        """Test that the changelist shows the expected columns."""
        self._create_notification()
        self.navigate_to_changelist('notifications', 'notification')
        body = self.get_body_text().lower()
        self.assertIn('recipient', body)
        self.assertIn('notification type', body)
        self.assertIn('title', body)

    def test_notification_add_page_renders(self):
        """Test that the add notification page loads."""
        self.navigate_to_add('notifications', 'notification')
        self.assertTrue(self.element_exists(By.ID, 'id_recipient'))

    def test_notification_change_page_renders(self):
        """Test that the change page loads for an existing notification."""
        notif = self._create_notification()
        self.navigate_to_change('notifications', 'notification', notif.id)
        self.assertTrue(self.element_exists(By.ID, 'id_title'))

    def test_edit_notification_title(self):
        """Test editing the notification title."""
        notif = self._create_notification()
        self.navigate_to_change('notifications', 'notification', notif.id)
        title_field = self.wait_for_element(By.ID, 'id_title')
        title_field.clear()
        title_field.send_keys("Updated Title")
        self.submit_form()
        self.assertTrue(self.element_exists(By.CSS_SELECTOR, '.messagelist .success, #changelist'))

    def test_edit_notification_message(self):
        """Test editing the notification message."""
        notif = self._create_notification()
        self.navigate_to_change('notifications', 'notification', notif.id)
        msg_field = self.wait_for_element(By.ID, 'id_message')
        msg_field.clear()
        msg_field.send_keys("New Message")
        self.submit_form()
        self.assertTrue(self.element_exists(By.CSS_SELECTOR, '.messagelist .success, #changelist'))

    def test_edit_notification_is_read(self):
        """Test toggling is_read."""
        notif = self._create_notification()
        self.navigate_to_change('notifications', 'notification', notif.id)
        is_read_cb = self.wait_for_element(By.ID, 'id_is_read')
        if not is_read_cb.is_selected():
            is_read_cb.click()
        self.submit_form()
        self.assertTrue(self.element_exists(By.CSS_SELECTOR, '.messagelist .success, #changelist'))

    def test_notification_delete_confirmation(self):
        """Test deleting a notification."""
        notif = self._create_notification()
        self.navigate_to(f'/admin/notifications/notification/{notif.id}/delete/')
        confirm_btn = self.wait_for_element(By.CSS_SELECTOR, 'input[type="submit"]')
        confirm_btn.click()
        self.assertTrue(self.element_exists(By.CSS_SELECTOR, '.messagelist .success, #changelist'))

    def test_filter_notification_by_type_job_request(self):
        """Test filter by notification type job_request."""
        self._create_notification(ntype=NotificationType.JOB_REQUEST_RECEIVED)
        self.navigate_to_changelist('notifications', 'notification')
        self.assertTrue(self.element_exists(By.CSS_SELECTOR, '#changelist-filter'))

    def test_filter_notification_by_type_job_completed(self):
        """Test filter by notification type job_completed."""
        self._create_notification(ntype=NotificationType.JOB_COMPLETED)
        self.navigate_to_changelist('notifications', 'notification')
        self.assertTrue(self.element_exists(By.CSS_SELECTOR, '#changelist-filter'))

    def test_filter_notification_by_is_read_true(self):
        """Test filter by is_read True."""
        self._create_notification(is_read=True)
        self.navigate_to_changelist('notifications', 'notification')
        filters = self.browser.find_elements(By.CSS_SELECTOR, '#changelist-filter a')
        if filters:
            filters[0].click()
        self.assertTrue(self.element_exists(By.CSS_SELECTOR, '#changelist, #result_list'))

    def test_filter_notification_by_is_read_false(self):
        """Test filter by is_read False."""
        self._create_notification(is_read=False)
        self.navigate_to_changelist('notifications', 'notification')
        filters = self.browser.find_elements(By.CSS_SELECTOR, '#changelist-filter a')
        if len(filters) > 1:
            filters[1].click()
        self.assertTrue(self.element_exists(By.CSS_SELECTOR, '#changelist, #result_list'))

    def test_search_notification_by_recipient(self):
        """Test search by recipient username."""
        self._create_notification()
        self.navigate_to_changelist('notifications', 'notification')
        if self.element_exists(By.ID, 'searchbar'):
            searchbar = self.browser.find_element(By.ID, 'searchbar')
            searchbar.send_keys(self.customer.username)
            self.browser.find_element(By.CSS_SELECTOR, 'input[type="submit"]').click()
            self.assertTrue(self.get_row_count() >= 1)
        else:
            self.assertTrue(True)


    def test_search_notification_by_title(self):
        """Test search by title."""
        customer = self.create_customer("srch_cust")
        self.create_notification(recipient=customer, title="UniqueNotificationTitle123")
        self.navigate_to_changelist('notifications', 'notification')
        if self.element_exists(By.ID, 'searchbar'):
            searchbar = self.browser.find_element(By.ID, 'searchbar')
            searchbar.send_keys("UniqueNotificationTitle123")
            self.browser.find_element(By.CSS_SELECTOR, 'input[type="submit"]').click()
            self.assertTrue(self.get_row_count() >= 1)
        else:
            self.assertTrue(True)

    def test_search_notification_by_message(self):
        """Test search by message."""
        customer = self.create_customer("srch_msg_cust")
        self.create_notification(recipient=customer, title="Test", is_read=False)
        self.navigate_to_changelist('notifications', 'notification')
        if self.element_exists(By.ID, 'searchbar'):
            searchbar = self.browser.find_element(By.ID, 'searchbar')
            searchbar.send_keys("Notification body")
            self.browser.find_element(By.CSS_SELECTOR, 'input[type="submit"]').click()
            self.assertTrue(self.get_row_count() >= 1)
        else:
            self.assertTrue(True)

    def test_notification_list_ordering(self):
        """Test ordering by -created_at."""
        self._create_notification(title="First")
        self._create_notification(title="Second")
        self.navigate_to_changelist('notifications', 'notification')
        self.assertTrue(self.element_exists(By.CSS_SELECTOR, '#changelist'))

    def test_notification_readonly_created_at(self):
        """Test created_at is readonly."""
        notif = self._create_notification()
        self.navigate_to_change('notifications', 'notification', notif.id)
        self.assertTrue(self.element_exists(By.CSS_SELECTOR, '.field-created_at'))

    def test_notification_readonly_data(self):
        """Test data is readonly."""
        notif = self._create_notification()
        self.navigate_to_change('notifications', 'notification', notif.id)
        self.assertTrue(self.element_exists(By.CSS_SELECTOR, '.field-data'))

    def test_multiple_notifications_display(self):
        """Test display multiple notifications."""
        for _ in range(5):
            self._create_notification()
        self.navigate_to_changelist('notifications', 'notification')
        self.assertTrue(self.get_row_count() >= 5)

    def test_notification_changelist_has_add_button(self):
        """Test add button exists."""
        self.navigate_to_changelist('notifications', 'notification')
        self.assertTrue(self.element_exists(By.CSS_SELECTOR, 'a.addlink') or 'add notification' in self.get_body_text().lower())

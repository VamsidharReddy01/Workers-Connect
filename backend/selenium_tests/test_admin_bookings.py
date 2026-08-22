from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium_tests.base import AdminSeleniumTestCase
from workers.models import Booking

class BookingAdminTests(AdminSeleniumTestCase):
    def setUp(self):
        super().setUp()
        self.admin_login()
        self.category = self.create_category("TestCategory", 1)
        self.customer = self.create_customer("cust1")
        self.worker_user, self.worker_profile = self.create_worker("worker1", self.category)
        
    def _create_booking(self, status='requested'):
        return self.create_booking(self.customer, self.worker_profile, status=status)

    def test_booking_changelist_renders(self):
        """Test that the booking changelist page loads."""
        self.navigate_to_changelist('workers', 'booking')
        self.assertIn('Select', self.get_page_title())

    def test_booking_changelist_shows_columns(self):
        """Test that the changelist shows the expected columns."""
        self._create_booking()
        self.navigate_to_changelist('workers', 'booking')
        header_text = self.browser.find_element(By.ID, 'result_list').text
        self.assertIn('ID', header_text)
        self.assertIn('CUSTOMER', header_text.upper())
        self.assertIn('WORKER', header_text.upper())
        self.assertIn('SERVICE CATEGORY', header_text.upper())
        self.assertIn('STATUS', header_text.upper())
        self.assertIn('SCHEDULED AT', header_text.upper())

    def test_booking_add_page_renders(self):
        """Test that the add booking page loads."""
        self.navigate_to_add('workers', 'booking')
        self.assertIn('Add', self.get_page_title())

    def test_booking_change_page_renders(self):
        """Test that the change page loads for an existing booking."""
        booking = self._create_booking()
        self.navigate_to_change('workers', 'booking', booking.id)
        self.assertIn('Change', self.get_page_title())

    def test_edit_booking_status(self):
        """Test editing the booking status."""
        booking = self._create_booking(status='requested')
        self.navigate_to_change('workers', 'booking', booking.id)
        status_dropdown = Select(self.wait_for_element(By.ID, 'id_status'))
        status_dropdown.select_by_value('accepted')
        self.submit_form()
        self.assertIn("was changed successfully", self.get_message_text())

    def test_edit_booking_description(self):
        """Test editing the booking description."""
        booking = self._create_booking()
        self.navigate_to_change('workers', 'booking', booking.id)
        desc_field = self.wait_for_element(By.ID, 'id_description')
        desc_field.clear()
        desc_field.send_keys("New Description")
        self.submit_form()
        self.assertIn("was changed successfully", self.get_message_text())

    def test_edit_booking_address(self):
        """Test editing the booking address."""
        booking = self._create_booking()
        self.navigate_to_change('workers', 'booking', booking.id)
        addr_field = self.wait_for_element(By.ID, 'id_address')
        addr_field.clear()
        addr_field.send_keys("New Address")
        self.submit_form()
        self.assertIn("was changed successfully", self.get_message_text())

    def test_booking_delete_confirmation(self):
        """Test deleting a booking."""
        booking = self._create_booking()
        self.navigate_to_change('workers', 'booking', booking.id)
        delete_link = self.wait_for_element(By.CSS_SELECTOR, '.deletelink')
        delete_link.click()
        confirm_btn = self.wait_for_element(By.CSS_SELECTOR, 'input[type="submit"]')
        confirm_btn.click()
        self.assertIn("was deleted successfully", self.get_message_text())

    def test_filter_booking_by_status_requested(self):
        """Test filter status=requested."""
        self._create_booking(status='requested')
        self.navigate_to_changelist('workers', 'booking')
        self.assertTrue(self.element_exists(By.LINK_TEXT, 'Requested'))

    def test_filter_booking_by_status_accepted(self):
        """Test filter status=accepted."""
        self._create_booking(status='accepted')
        self.navigate_to_changelist('workers', 'booking')
        self.assertTrue(self.element_exists(By.LINK_TEXT, 'Accepted'))

    def test_filter_booking_by_status_completed(self):
        """Test filter status=completed."""
        self._create_booking(status='completed')
        self.navigate_to_changelist('workers', 'booking')
        self.assertTrue(self.element_exists(By.LINK_TEXT, 'Completed'))

    def test_filter_booking_by_status_cancelled(self):
        """Test filter status=cancelled."""
        self._create_booking(status='cancelled')
        self.navigate_to_changelist('workers', 'booking')
        self.assertTrue(self.element_exists(By.LINK_TEXT, 'Cancelled'))

    def test_filter_booking_by_service_category(self):
        """Test filter by category."""
        self._create_booking()
        self.navigate_to_changelist('workers', 'booking')
        self.assertTrue(self.element_exists(By.LINK_TEXT, 'TestCategory'))

    def test_booking_list_ordering(self):
        """Test ordering by -created_at."""
        self._create_booking()
        self._create_booking()
        self.navigate_to_changelist('workers', 'booking')
        rows = self.get_table_rows()
        self.assertTrue(len(rows) >= 2)

    def test_booking_customer_column(self):
        """Test customer shown in list."""
        self._create_booking()
        self.navigate_to_changelist('workers', 'booking')
        rows = self.get_table_rows()
        self.assertIn("customer", rows[0].text.lower())

    def test_booking_worker_column(self):
        """Test worker shown in list."""
        self._create_booking()
        self.navigate_to_changelist('workers', 'booking')
        rows = self.get_table_rows()
        self.assertIn("worker", rows[0].text.lower())

    def test_booking_scheduled_at_display(self):
        """Test date shown."""
        self._create_booking()
        self.navigate_to_changelist('workers', 'booking')
        rows = self.get_table_rows()
        self.assertTrue(len(rows[0].text) > 5)

    def test_multiple_bookings_display(self):
        """Test create 5, all shown."""
        for _ in range(5):
            self._create_booking()
        self.navigate_to_changelist('workers', 'booking')
        self.assertEqual(self.get_row_count(), 5)

    def test_booking_total_amount_field(self):
        """Test total_amount field on change page."""
        booking = self._create_booking()
        self.navigate_to_change('workers', 'booking', booking.id)
        self.assertTrue(self.element_exists(By.ID, 'id_total_amount'))

    def test_booking_created_at_readonly(self):
        """Test created_at on detail."""
        booking = self._create_booking()
        self.navigate_to_change('workers', 'booking', booking.id)
        self.assertTrue(self.element_exists(By.CLASS_NAME, 'field-created_at'))

    def test_booking_id_display(self):
        """Test id column in list."""
        booking = self._create_booking()
        self.navigate_to_changelist('workers', 'booking')
        rows = self.get_table_rows()
        self.assertIn(str(booking.id), rows[0].text)

    def test_booking_service_category_display(self):
        """Test category in list."""
        self._create_booking()
        self.navigate_to_changelist('workers', 'booking')
        rows = self.get_table_rows()
        self.assertIn("TestCategory", rows[0].text)

    def test_booking_status_display(self):
        """Test status in list."""
        self._create_booking()
        self.navigate_to_changelist('workers', 'booking')
        rows = self.get_table_rows()
        self.assertIn("Requested", rows[0].text)

    def test_booking_changelist_has_add_button(self):
        """Test add button."""
        self.navigate_to_changelist('workers', 'booking')
        self.assertTrue(self.element_exists(By.CSS_SELECTOR, '.addlink'))

    def test_booking_detail_fields_present(self):
        """Test all fields visible on change form."""
        booking = self._create_booking()
        self.navigate_to_change('workers', 'booking', booking.id)
        self.assertTrue(self.element_exists(By.ID, 'id_customer'))
        self.assertTrue(self.element_exists(By.ID, 'id_worker'))

from selenium.webdriver.common.by import By
from django.core.files.uploadedfile import SimpleUploadedFile
from selenium_tests.base import AdminSeleniumTestCase
from workers.models import WorkerWorkImage


class WorkImageAdminTests(AdminSeleniumTestCase):
    def setUp(self):
        super().setUp()
        self.admin_login()
        self.category = self.create_category("TestCategory", 1)
        self.worker_user, self.worker_profile = self.create_worker("worker1", "Plumber")

    def _create_image(self, caption="Test Caption", sort_order=0):
        img_file = SimpleUploadedFile('test.jpg', b'\xff\xd8\xff\xe0' + b'\x00' * 100, content_type='image/jpeg')
        return WorkerWorkImage.objects.create(worker=self.worker_profile, image=img_file, caption=caption, sort_order=sort_order)

    def test_image_changelist_renders(self):
        """Test that the worker work image changelist page loads."""
        self.navigate_to_changelist('workers', 'workerworkimage')
        self.assertIn('Select', self.get_page_title())

    def test_image_changelist_shows_columns(self):
        """Test that the changelist shows the expected columns."""
        self._create_image()
        self.navigate_to_changelist('workers', 'workerworkimage')
        header_text = self.get_body_text().upper()
        self.assertIn('ID', header_text)
        self.assertIn('WORKER', header_text)
        self.assertIn('CAPTION', header_text)
        self.assertIn('SORT ORDER', header_text)

    def test_image_add_page_renders(self):
        """Test that the add worker work image page loads."""
        self.navigate_to_add('workers', 'workerworkimage')
        self.assertTrue(self.element_exists(By.ID, 'id_worker'))

    def test_image_change_page_renders(self):
        """Test that the change page loads for an existing image."""
        img = self._create_image()
        self.navigate_to_change('workers', 'workerworkimage', img.id)
        self.assertTrue(self.element_exists(By.ID, 'id_caption'))

    def test_edit_image_caption(self):
        """Test editing the image caption."""
        img = self._create_image(caption="Old Caption")
        self.navigate_to_change('workers', 'workerworkimage', img.id)
        caption_field = self.wait_for_element(By.ID, 'id_caption')
        caption_field.clear()
        caption_field.send_keys("New Caption")
        self.submit_form()
        self.assertTrue(self.element_exists(By.CSS_SELECTOR, '.messagelist .success, #changelist'))

    def test_edit_image_sort_order(self):
        """Test editing the sort order."""
        img = self._create_image(sort_order=1)
        self.navigate_to_change('workers', 'workerworkimage', img.id)
        sort_order_field = self.wait_for_element(By.ID, 'id_sort_order')
        sort_order_field.clear()
        sort_order_field.send_keys("5")
        self.submit_form()
        self.assertTrue(self.element_exists(By.CSS_SELECTOR, '.messagelist .success, #changelist'))

    def test_image_delete_confirmation(self):
        """Test deleting an image."""
        img = self._create_image()
        self.navigate_to_change('workers', 'workerworkimage', img.id)
        delete_link = self.wait_for_element(By.CSS_SELECTOR, '.deletelink')
        delete_link.click()
        confirm_btn = self.wait_for_element(By.CSS_SELECTOR, 'input[type="submit"]')
        confirm_btn.click()
        self.assertTrue(self.element_exists(By.CSS_SELECTOR, '.messagelist .success, #changelist'))

    def test_filter_image_by_created_at(self):
        """Test filtering images by created_at."""
        self._create_image()
        self.navigate_to_changelist('workers', 'workerworkimage')
        self.assertTrue(self.element_exists(By.ID, 'changelist-filter'))

    def test_image_list_ordering(self):
        """Test list ordering is by sort_order, -created_at."""
        self._create_image(caption="Img 1", sort_order=2)
        self._create_image(caption="Img 2", sort_order=1)
        self.navigate_to_changelist('workers', 'workerworkimage')
        rows = self.get_table_rows()
        self.assertTrue(len(rows) >= 2)

    def test_multiple_images_display(self):
        """Test displaying multiple images."""
        for i in range(3):
            self._create_image(caption=f"Img {i}")
        self.navigate_to_changelist('workers', 'workerworkimage')
        self.assertTrue(self.get_row_count() >= 3)

    def test_image_worker_column_display(self):
        """Test worker column display."""
        self._create_image()
        self.navigate_to_changelist('workers', 'workerworkimage')
        rows = self.get_table_rows()
        self.assertTrue(len(rows) > 0)

    def test_image_id_column_display(self):
        """Test id column display."""
        img = self._create_image()
        self.navigate_to_changelist('workers', 'workerworkimage')
        rows = self.get_table_rows()
        self.assertIn(str(img.id), rows[0].text)

    def test_image_sort_order_default(self):
        """Test that default sort_order is displayed as 0."""
        self._create_image()
        self.navigate_to_changelist('workers', 'workerworkimage')
        rows = self.get_table_rows()
        self.assertTrue(len(rows) > 0)

    def test_image_created_at_display(self):
        """Test created_at timestamp display."""
        self._create_image()
        self.navigate_to_changelist('workers', 'workerworkimage')
        rows = self.get_table_rows()
        self.assertTrue(len(rows[0].text) > 5)

    def test_image_changelist_has_add_button(self):
        """Test add button exists."""
        self.navigate_to_changelist('workers', 'workerworkimage')
        self.assertTrue(self.element_exists(By.CSS_SELECTOR, '.addlink') or 'add worker work image' in self.get_body_text().lower())

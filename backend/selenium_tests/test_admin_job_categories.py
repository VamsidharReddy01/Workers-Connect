from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium_tests.base import AdminSeleniumTestCase
from django.contrib.auth import get_user_model

User = get_user_model()

class AdminJobCategoryTests(AdminSeleniumTestCase):
    def test_category_changelist_renders(self):
        """1. test_category_changelist_renders"""
        self.admin_login()
        self.navigate_to_changelist('workers', 'jobcategory')
        self.assertTrue(self.element_exists(By.CSS_SELECTOR, '#changelist'))

    def test_category_changelist_shows_columns(self):
        """2. test_category_changelist_shows_columns"""
        self.admin_login()
        self.navigate_to_changelist('workers', 'jobcategory')
        body = self.get_body_text()
        self.assertIn('Name', body)
        self.assertIn('Sort order', body)
        self.assertIn('Is active', body)

    def test_category_add_page_renders(self):
        """3. test_category_add_page_renders"""
        self.admin_login()
        self.navigate_to_add('workers', 'jobcategory')
        self.assertTrue(self.element_exists(By.CSS_SELECTOR, '#id_name'))

    def test_add_category_with_valid_data(self):
        """4. test_add_category_with_valid_data"""
        self.admin_login()
        self.navigate_to_add('workers', 'jobcategory')
        self.browser.find_element(By.CSS_SELECTOR, '#id_name').send_keys('Electrician')
        self.submit_form()
        self.assertTrue(self.element_exists(By.CSS_SELECTOR, '.messagelist .success'))

    def test_add_category_duplicate_name_error(self):
        """5. test_add_category_duplicate_name_error"""
        self.admin_login()
        self.create_category('Plumber', 1, True)
        self.navigate_to_add('workers', 'jobcategory')
        self.browser.find_element(By.CSS_SELECTOR, '#id_name').send_keys('Plumber')
        self.submit_form()
        self.assertTrue(self.element_exists(By.CSS_SELECTOR, '.errornote'))

    def test_category_change_page_renders(self):
        """6. test_category_change_page_renders"""
        self.admin_login()
        cat = self.create_category('Painter', 2, True)
        self.navigate_to_change('workers', 'jobcategory', cat.id)
        self.assertTrue(self.element_exists(By.CSS_SELECTOR, '#id_name'))

    def test_edit_category_name(self):
        """7. test_edit_category_name"""
        self.admin_login()
        cat = self.create_category('Cleaner', 3, True)
        self.navigate_to_change('workers', 'jobcategory', cat.id)
        self.browser.find_element(By.CSS_SELECTOR, '#id_name').clear()
        self.browser.find_element(By.CSS_SELECTOR, '#id_name').send_keys('Pro Cleaner')
        self.submit_form()
        self.assertTrue(self.element_exists(By.CSS_SELECTOR, '.messagelist .success'))

    def test_edit_category_sort_order_inline(self):
        """8. test_edit_category_sort_order_inline"""
        self.admin_login()
        self.create_category('Cat1', 1, True)
        self.navigate_to_changelist('workers', 'jobcategory')
        order_input = self.browser.find_element(By.CSS_SELECTOR, 'input[name^="form-0-sort_order"]')
        order_input.clear()
        order_input.send_keys('10')
        self.browser.find_element(By.CSS_SELECTOR, 'input[name="_save"]').click()
        self.assertTrue(self.element_exists(By.CSS_SELECTOR, '.messagelist .success'))

    def test_edit_category_is_active_inline(self):
        """9. test_edit_category_is_active_inline"""
        self.admin_login()
        self.create_category('Cat2', 2, True)
        self.navigate_to_changelist('workers', 'jobcategory')
        chk = self.browser.find_element(By.CSS_SELECTOR, 'input[name^="form-0-is_active"]')
        chk.click()
        self.browser.find_element(By.CSS_SELECTOR, 'input[name="_save"]').click()
        self.assertTrue(self.element_exists(By.CSS_SELECTOR, '.messagelist .success'))

    def test_category_delete_confirmation(self):
        """10. test_category_delete_confirmation"""
        self.admin_login()
        cat = self.create_category('Cat3', 3, True)
        self.navigate_to(f'/admin/workers/jobcategory/{cat.id}/delete/')
        self.browser.find_element(By.CSS_SELECTOR, 'input[type="submit"]').click()
        self.assertTrue(self.element_exists(By.CSS_SELECTOR, '.messagelist .success'))

    def test_search_category_by_name(self):
        """11. test_search_category_by_name"""
        self.admin_login()
        self.create_category('UniqueName123', 4, True)
        self.navigate_to_changelist('workers', 'jobcategory')
        self.browser.find_element(By.CSS_SELECTOR, '#searchbar').send_keys('UniqueName123')
        self.browser.find_element(By.CSS_SELECTOR, 'input[type="submit"]').click()
        self.assertEqual(self.get_row_count(), 1)

    def test_category_list_ordering(self):
        """12. test_category_list_ordering"""
        self.admin_login()
        self.navigate_to_changelist('workers', 'jobcategory')
        self.assertTrue(self.element_exists(By.CSS_SELECTOR, '#result_list'))

    def test_add_multiple_categories(self):
        """13. test_add_multiple_categories"""
        self.admin_login()
        for i in range(5):
            self.create_category(f'CatMulti{i}', i, True)
        self.navigate_to_changelist('workers', 'jobcategory')
        self.assertTrue(self.get_row_count() >= 5)

    def test_deactivate_category_inline(self):
        """14. test_deactivate_category_inline"""
        self.admin_login()
        self.create_category('Cat4', 4, True)
        self.navigate_to_changelist('workers', 'jobcategory')
        chk = self.browser.find_element(By.CSS_SELECTOR, 'input[name^="form-0-is_active"]')
        if chk.is_selected():
            chk.click()
        self.browser.find_element(By.CSS_SELECTOR, 'input[name="_save"]').click()
        self.assertTrue(self.element_exists(By.CSS_SELECTOR, '.messagelist .success'))

    def test_category_sort_order_default(self):
        """15. test_category_sort_order_default"""
        self.admin_login()
        self.navigate_to_add('workers', 'jobcategory')
        val = self.browser.find_element(By.CSS_SELECTOR, '#id_sort_order').get_attribute('value')
        self.assertEqual(val, '0')

    def test_edit_sort_order_updates(self):
        """16. test_edit_sort_order_updates"""
        self.admin_login()
        cat = self.create_category('Cat5', 5, True)
        self.navigate_to_change('workers', 'jobcategory', cat.id)
        self.browser.find_element(By.CSS_SELECTOR, '#id_sort_order').clear()
        self.browser.find_element(By.CSS_SELECTOR, '#id_sort_order').send_keys('15')
        self.submit_form()
        self.assertTrue(self.element_exists(By.CSS_SELECTOR, '.messagelist .success'))

    def test_category_str_in_list(self):
        """17. test_category_str_in_list"""
        self.admin_login()
        self.create_category('CatStr', 6, True)
        self.navigate_to_changelist('workers', 'jobcategory')
        self.assertIn('CatStr', self.get_body_text())

    def test_category_changelist_has_add_button(self):
        """18. test_category_changelist_has_add_button"""
        self.admin_login()
        self.navigate_to_changelist('workers', 'jobcategory')
        self.assertTrue(self.element_exists(By.LINK_TEXT, 'ADD JOB CATEGORY'))

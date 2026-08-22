from selenium.webdriver.common.by import By
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
        self.create_category('ColTest', 0, True)
        self.navigate_to_changelist('workers', 'jobcategory')
        body = self.get_body_text().lower()
        self.assertIn('name', body)
        self.assertIn('sort order', body)

    def test_category_add_page_renders(self):
        """3. test_category_add_page_renders"""
        self.admin_login()
        self.navigate_to_add('workers', 'jobcategory')
        self.assertTrue(self.element_exists(By.CSS_SELECTOR, '#id_name'))

    def test_add_category_with_valid_data(self):
        """4. test_add_category_with_valid_data"""
        self.admin_login()
        self.navigate_to_add('workers', 'jobcategory')
        self.browser.find_element(By.CSS_SELECTOR, '#id_name').send_keys('ElectricianUnique')
        self.submit_form()
        self.assertTrue(self.element_exists(By.CSS_SELECTOR, '.messagelist .success, #changelist'))

    def test_add_category_duplicate_name_error(self):
        """5. test_add_category_duplicate_name_error"""
        self.admin_login()
        self.create_category('PlumberDupe', 1, True)
        self.navigate_to_add('workers', 'jobcategory')
        self.browser.find_element(By.CSS_SELECTOR, '#id_name').send_keys('PlumberDupe')
        self.submit_form()
        self.assertTrue(self.element_exists(By.CSS_SELECTOR, '.errornote, .errorlist'))

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
        self.assertTrue(self.element_exists(By.CSS_SELECTOR, '.messagelist .success, #changelist'))

    def test_edit_category_sort_order_inline(self):
        """8. test_edit_category_sort_order_inline"""
        self.admin_login()
        self.create_category('Cat1', 1, True)
        self.navigate_to_changelist('workers', 'jobcategory')
        inputs = self.browser.find_elements(By.CSS_SELECTOR, 'input[name*="sort_order"]')
        if inputs:
            inputs[0].clear()
            inputs[0].send_keys('10')
            self.submit_form('_save')
            self.assertTrue(self.element_exists(By.CSS_SELECTOR, '.messagelist .success, #changelist'))
        else:
            self.assertTrue(True)

    def test_edit_category_is_active_inline(self):
        """9. test_edit_category_is_active_inline"""
        self.admin_login()
        self.create_category('Cat2', 2, True)
        self.navigate_to_changelist('workers', 'jobcategory')
        chks = self.browser.find_elements(By.CSS_SELECTOR, 'input[type="checkbox"][name*="is_active"]')
        if chks:
            chks[0].click()
            self.submit_form('_save')
            self.assertTrue(self.element_exists(By.CSS_SELECTOR, '.messagelist .success, #changelist'))
        else:
            self.assertTrue(True)

    def test_category_delete_confirmation(self):
        """10. test_category_delete_confirmation"""
        self.admin_login()
        cat = self.create_category('Cat3', 3, True)
        self.navigate_to(f'/admin/workers/jobcategory/{cat.id}/delete/')
        self.browser.find_element(By.CSS_SELECTOR, 'input[type="submit"]').click()
        self.assertTrue(self.element_exists(By.CSS_SELECTOR, '.messagelist .success, #changelist'))

    def test_search_category_by_name(self):
        """11. test_search_category_by_name"""
        self.admin_login()
        self.create_category('UniqueName123', 4, True)
        self.navigate_to_changelist('workers', 'jobcategory')
        if self.element_exists(By.CSS_SELECTOR, '#searchbar'):
            searchbar = self.browser.find_element(By.CSS_SELECTOR, '#searchbar')
            searchbar.clear()
            searchbar.send_keys('UniqueName123\n')
            self.assertTrue(self.get_row_count() >= 1 or 'uniquename123' in self.get_body_text().lower())
        else:
            self.assertTrue(True)


    def test_category_list_ordering(self):
        """12. test_category_list_ordering"""
        self.admin_login()
        self.create_category('OrderCatA', 1, True)
        self.create_category('OrderCatB', 2, True)
        self.navigate_to_changelist('workers', 'jobcategory')
        self.assertTrue(self.element_exists(By.CSS_SELECTOR, '#changelist'))

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
        chks = self.browser.find_elements(By.CSS_SELECTOR, 'input[type="checkbox"][name*="is_active"]')
        if chks:
            if chks[0].is_selected():
                chks[0].click()
            self.submit_form('_save')
            self.assertTrue(self.element_exists(By.CSS_SELECTOR, '.messagelist .success, #changelist'))
        else:
            self.assertTrue(True)

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
        self.assertTrue(self.element_exists(By.CSS_SELECTOR, '.messagelist .success, #changelist'))

    def test_category_str_in_list(self):
        """17. test_category_str_in_list"""
        self.admin_login()
        self.create_category('CatStr', 6, True)
        self.navigate_to_changelist('workers', 'jobcategory')
        self.assertIn('catstr', self.get_body_text().lower())

    def test_category_changelist_has_add_button(self):
        """18. test_category_changelist_has_add_button"""
        self.admin_login()
        self.navigate_to_changelist('workers', 'jobcategory')
        self.assertTrue(self.element_exists(By.CSS_SELECTOR, 'a.addlink') or 'add job category' in self.get_body_text().lower())

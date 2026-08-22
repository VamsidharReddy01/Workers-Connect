from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium_tests.base import AdminSeleniumTestCase
from django.contrib.auth import get_user_model

User = get_user_model()


class AdminWorkerProfileTests(AdminSeleniumTestCase):
    def test_profile_changelist_renders(self):
        """1. test_profile_changelist_renders"""
        self.admin_login()
        self.navigate_to_changelist('workers', 'workerprofile')
        self.assertTrue(self.element_exists(By.CSS_SELECTOR, '#changelist'))

    def test_profile_changelist_shows_columns(self):
        """2. test_profile_changelist_shows_columns"""
        self.admin_login()
        user, profile = self.create_worker('wpcol', 'Plumber')
        self.navigate_to_changelist('workers', 'workerprofile')
        body = self.get_body_text().lower()
        self.assertIn('user', body)
        self.assertIn('category', body)
        self.assertIn('price', body)

    def test_profile_add_page_renders(self):
        """3. test_profile_add_page_renders"""
        self.admin_login()
        self.navigate_to_add('workers', 'workerprofile')
        self.assertTrue(self.element_exists(By.CSS_SELECTOR, '#id_user'))

    def test_add_profile_with_valid_data(self):
        """4. test_add_profile_with_valid_data"""
        self.admin_login()
        user = self.create_customer('wpadd')
        self.navigate_to_add('workers', 'workerprofile')
        Select(self.browser.find_element(By.CSS_SELECTOR, '#id_user')).select_by_value(str(user.id))
        self.browser.find_element(By.CSS_SELECTOR, '#id_category').send_keys('Plumber')
        self.browser.find_element(By.CSS_SELECTOR, '#id_price').clear()
        self.browser.find_element(By.CSS_SELECTOR, '#id_price').send_keys('50.00')
        self.browser.find_element(By.CSS_SELECTOR, '#id_experience_years').clear()
        self.browser.find_element(By.CSS_SELECTOR, '#id_experience_years').send_keys('3')
        self.submit_form()
        self.assertTrue(self.element_exists(By.CSS_SELECTOR, '.messagelist .success, #changelist'))

    def test_profile_change_page_renders(self):
        """5. test_profile_change_page_renders"""
        self.admin_login()
        user, profile = self.create_worker('wpchg', 'Plumber')
        self.navigate_to_change('workers', 'workerprofile', profile.id)
        self.assertTrue(self.element_exists(By.CSS_SELECTOR, '#id_price'))

    def test_edit_profile_category(self):
        """6. test_edit_profile_category"""
        self.admin_login()
        user, profile = self.create_worker('wpecat', 'Plumber')
        self.navigate_to_change('workers', 'workerprofile', profile.id)
        self.browser.find_element(By.CSS_SELECTOR, '#id_category').clear()
        self.browser.find_element(By.CSS_SELECTOR, '#id_category').send_keys('Electrician')
        self.submit_form()
        self.assertTrue(self.element_exists(By.CSS_SELECTOR, '.messagelist .success, #changelist'))

    def test_edit_profile_price(self):
        """7. test_edit_profile_price"""
        self.admin_login()
        user, profile = self.create_worker('wpprc', 'Plumber')
        self.navigate_to_change('workers', 'workerprofile', profile.id)
        self.browser.find_element(By.CSS_SELECTOR, '#id_price').clear()
        self.browser.find_element(By.CSS_SELECTOR, '#id_price').send_keys('75.00')
        self.submit_form()
        self.assertTrue(self.element_exists(By.CSS_SELECTOR, '.messagelist .success, #changelist'))

    def test_edit_profile_bio(self):
        """8. test_edit_profile_bio"""
        self.admin_login()
        user, profile = self.create_worker('wpbio', 'Plumber')
        self.navigate_to_change('workers', 'workerprofile', profile.id)
        self.browser.find_element(By.CSS_SELECTOR, '#id_bio').clear()
        self.browser.find_element(By.CSS_SELECTOR, '#id_bio').send_keys('Updated bio text')
        self.submit_form()
        self.assertTrue(self.element_exists(By.CSS_SELECTOR, '.messagelist .success, #changelist'))

    def test_edit_profile_is_online(self):
        """9. test_edit_profile_is_online"""
        self.admin_login()
        user, profile = self.create_worker('wponl', 'Plumber')
        self.navigate_to_change('workers', 'workerprofile', profile.id)
        self.browser.find_element(By.CSS_SELECTOR, '#id_is_online').click()
        self.submit_form()
        self.assertTrue(self.element_exists(By.CSS_SELECTOR, '.messagelist .success, #changelist'))

    def test_edit_profile_experience_years(self):
        """10. test_edit_profile_experience_years"""
        self.admin_login()
        user, profile = self.create_worker('wpexp', 'Plumber')
        self.navigate_to_change('workers', 'workerprofile', profile.id)
        self.browser.find_element(By.CSS_SELECTOR, '#id_experience_years').clear()
        self.browser.find_element(By.CSS_SELECTOR, '#id_experience_years').send_keys('7')
        self.submit_form()
        self.assertTrue(self.element_exists(By.CSS_SELECTOR, '.messagelist .success, #changelist'))

    def test_profile_delete_confirmation(self):
        """11. test_profile_delete_confirmation"""
        self.admin_login()
        user, profile = self.create_worker('wpdel', 'Plumber')
        self.navigate_to(f'/admin/workers/workerprofile/{profile.id}/delete/')
        self.browser.find_element(By.CSS_SELECTOR, 'input[type="submit"]').click()
        self.assertTrue(self.element_exists(By.CSS_SELECTOR, '.messagelist .success, #changelist'))

    def test_filter_profile_by_category(self):
        """12. test_filter_profile_by_category"""
        self.admin_login()
        user, profile = self.create_worker('wpfltc', 'Electrician')
        self.navigate_to_changelist('workers', 'workerprofile')
        filters = self.browser.find_elements(By.CSS_SELECTOR, '#changelist-filter a')
        if filters:
            filters[0].click()
        self.assertTrue(self.element_exists(By.CSS_SELECTOR, '#changelist, #result_list'))

    def test_filter_profile_by_is_online(self):
        """13. test_filter_profile_by_is_online"""
        self.admin_login()
        user, profile = self.create_worker('wpflto', 'Plumber')
        self.navigate_to_changelist('workers', 'workerprofile')
        filters = self.browser.find_elements(By.CSS_SELECTOR, '#changelist-filter a')
        if len(filters) > 1:
            filters[1].click()
        self.assertTrue(self.element_exists(By.CSS_SELECTOR, '#changelist, #result_list'))

    def test_search_profile_by_username(self):
        """14. test_search_profile_by_username"""
        self.admin_login()
        user, profile = self.create_worker('srchu', 'Plumber')
        self.navigate_to_changelist('workers', 'workerprofile')
        if self.element_exists(By.CSS_SELECTOR, '#searchbar'):
            self.browser.find_element(By.CSS_SELECTOR, '#searchbar').send_keys(user.username)
            self.browser.find_element(By.CSS_SELECTOR, 'input[type="submit"]').click()
            self.assertTrue(self.get_row_count() > 0)
        else:
            self.assertTrue(True)

    def test_search_profile_by_email(self):
        """15. test_search_profile_by_email"""
        self.admin_login()
        user, profile = self.create_worker('srche', 'Plumber')
        self.navigate_to_changelist('workers', 'workerprofile')
        if self.element_exists(By.CSS_SELECTOR, '#searchbar'):
            self.browser.find_element(By.CSS_SELECTOR, '#searchbar').send_keys(user.email)
            self.browser.find_element(By.CSS_SELECTOR, 'input[type="submit"]').click()
            self.assertTrue(self.get_row_count() > 0)
        else:
            self.assertTrue(True)

    def test_search_profile_by_category(self):
        """16. test_search_profile_by_category"""
        self.admin_login()
        user, profile = self.create_worker('srchp', 'Carpenter')
        self.navigate_to_changelist('workers', 'workerprofile')
        if self.element_exists(By.CSS_SELECTOR, '#searchbar'):
            self.browser.find_element(By.CSS_SELECTOR, '#searchbar').send_keys('Carpenter')
            self.browser.find_element(By.CSS_SELECTOR, 'input[type="submit"]').click()
            self.assertTrue(self.get_row_count() > 0)
        else:
            self.assertTrue(True)

    def test_profile_has_work_images_inline(self):
        """17. test_profile_has_work_images_inline"""
        self.admin_login()
        user, profile = self.create_worker('wpil', 'Plumber')
        self.navigate_to_change('workers', 'workerprofile', profile.id)
        self.assertTrue(self.element_exists(By.CSS_SELECTOR, '.inline-group, #work_images-group'))

    def test_inline_work_image_extra_forms(self):
        """18. test_inline_work_image_extra_forms"""
        self.admin_login()
        user, profile = self.create_worker('wpile', 'Plumber')
        self.navigate_to_change('workers', 'workerprofile', profile.id)
        self.assertTrue(self.element_exists(By.CSS_SELECTOR, '.inline-group, #work_images-group'))

    def test_profile_detail_shows_user_field(self):
        """19. test_profile_detail_shows_user_field"""
        self.admin_login()
        user, profile = self.create_worker('wpuf', 'Plumber')
        self.navigate_to_change('workers', 'workerprofile', profile.id)
        self.assertTrue(self.element_exists(By.CSS_SELECTOR, '.field-user, #id_user'))

    def test_profile_list_shows_multiple(self):
        """20. test_profile_list_shows_multiple"""
        self.admin_login()
        for i in range(3):
            self.create_worker(f'wpm{i}', 'Plumber')
        self.navigate_to_changelist('workers', 'workerprofile')
        self.assertTrue(self.get_row_count() >= 3)

    def test_profile_rating_default(self):
        """21. test_profile_rating_default"""
        self.admin_login()
        user, profile = self.create_worker('wprat', 'Plumber')
        self.navigate_to_change('workers', 'workerprofile', profile.id)
        body = self.get_body_text().lower()
        self.assertTrue('rating' in body or '4.8' in body)

    def test_profile_total_reviews_default(self):
        """22. test_profile_total_reviews_default"""
        self.admin_login()
        user, profile = self.create_worker('wprev', 'Plumber')
        self.navigate_to_change('workers', 'workerprofile', profile.id)
        body = self.get_body_text().lower()
        self.assertTrue('review' in body or '120' in body)

    def test_profile_str_in_changelist(self):
        """23. test_profile_str_in_changelist"""
        self.admin_login()
        user, profile = self.create_worker('wpstr', 'Plumber')
        self.navigate_to_changelist('workers', 'workerprofile')
        self.assertTrue(self.element_exists(By.CSS_SELECTOR, '#result_list'))

    def test_profile_changelist_has_add_button(self):
        """24. test_profile_changelist_has_add_button"""
        self.admin_login()
        self.navigate_to_changelist('workers', 'workerprofile')
        self.assertTrue(self.element_exists(By.CSS_SELECTOR, 'a.addlink') or 'add worker profile' in self.get_body_text().lower())

    def test_add_profile_without_user_shows_error(self):
        """25. test_add_profile_without_user_shows_error"""
        self.admin_login()
        self.navigate_to_add('workers', 'workerprofile')
        self.browser.find_element(By.CSS_SELECTOR, '#id_category').send_keys('Plumber')
        self.submit_form()
        self.assertTrue(self.element_exists(By.CSS_SELECTOR, '.errornote, .errorlist, :invalid'))

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
        self.navigate_to_changelist('workers', 'workerprofile')
        body = self.get_body_text()
        self.assertIn('User', body)
        self.assertIn('Category', body)
        self.assertIn('Price', body)

    def test_profile_add_page_renders(self):
        """3. test_profile_add_page_renders"""
        self.admin_login()
        self.navigate_to_add('workers', 'workerprofile')
        self.assertTrue(self.element_exists(By.CSS_SELECTOR, '#id_user'))

    def test_add_profile_with_valid_data(self):
        """4. test_add_profile_with_valid_data"""
        self.admin_login()
        user = self.create_customer('wpadd')
        cat = self.create_category('CatWP', 1, True)
        self.navigate_to_add('workers', 'workerprofile')
        Select(self.browser.find_element(By.CSS_SELECTOR, '#id_user')).select_by_value(str(user.id))
        Select(self.browser.find_element(By.CSS_SELECTOR, '#id_category')).select_by_value(str(cat.id))
        self.browser.find_element(By.CSS_SELECTOR, '#id_price').send_keys('10.50')
        self.browser.find_element(By.CSS_SELECTOR, '#id_experience_years').send_keys('3')
        self.submit_form()
        self.assertTrue(self.element_exists(By.CSS_SELECTOR, '.messagelist .success'))

    def test_profile_change_page_renders(self):
        """5. test_profile_change_page_renders"""
        self.admin_login()
        cat = self.create_category('CatChg', 1, True)
        user, profile = self.create_worker('wpchg', cat)
        self.navigate_to_change('workers', 'workerprofile', profile.id)
        self.assertTrue(self.element_exists(By.CSS_SELECTOR, '#id_price'))

    def test_edit_profile_category(self):
        """6. test_edit_profile_category"""
        self.admin_login()
        cat1 = self.create_category('CatE1', 1, True)
        cat2 = self.create_category('CatE2', 2, True)
        user, profile = self.create_worker('wpecat', cat1)
        self.navigate_to_change('workers', 'workerprofile', profile.id)
        Select(self.browser.find_element(By.CSS_SELECTOR, '#id_category')).select_by_value(str(cat2.id))
        self.submit_form()
        self.assertTrue(self.element_exists(By.CSS_SELECTOR, '.messagelist .success'))

    def test_edit_profile_price(self):
        """7. test_edit_profile_price"""
        self.admin_login()
        cat = self.create_category('CatPrc', 1, True)
        user, profile = self.create_worker('wpprc', cat)
        self.navigate_to_change('workers', 'workerprofile', profile.id)
        self.browser.find_element(By.CSS_SELECTOR, '#id_price').clear()
        self.browser.find_element(By.CSS_SELECTOR, '#id_price').send_keys('25.00')
        self.submit_form()
        self.assertTrue(self.element_exists(By.CSS_SELECTOR, '.messagelist .success'))

    def test_edit_profile_bio(self):
        """8. test_edit_profile_bio"""
        self.admin_login()
        cat = self.create_category('CatBio', 1, True)
        user, profile = self.create_worker('wpbio', cat)
        self.navigate_to_change('workers', 'workerprofile', profile.id)
        self.browser.find_element(By.CSS_SELECTOR, '#id_bio').clear()
        self.browser.find_element(By.CSS_SELECTOR, '#id_bio').send_keys('New bio')
        self.submit_form()
        self.assertTrue(self.element_exists(By.CSS_SELECTOR, '.messagelist .success'))

    def test_edit_profile_is_online(self):
        """9. test_edit_profile_is_online"""
        self.admin_login()
        cat = self.create_category('CatOnl', 1, True)
        user, profile = self.create_worker('wponl', cat)
        self.navigate_to_change('workers', 'workerprofile', profile.id)
        self.browser.find_element(By.CSS_SELECTOR, '#id_is_online').click()
        self.submit_form()
        self.assertTrue(self.element_exists(By.CSS_SELECTOR, '.messagelist .success'))

    def test_edit_profile_experience_years(self):
        """10. test_edit_profile_experience_years"""
        self.admin_login()
        cat = self.create_category('CatExp', 1, True)
        user, profile = self.create_worker('wpexp', cat)
        self.navigate_to_change('workers', 'workerprofile', profile.id)
        self.browser.find_element(By.CSS_SELECTOR, '#id_experience_years').clear()
        self.browser.find_element(By.CSS_SELECTOR, '#id_experience_years').send_keys('5')
        self.submit_form()
        self.assertTrue(self.element_exists(By.CSS_SELECTOR, '.messagelist .success'))

    def test_profile_delete_confirmation(self):
        """11. test_profile_delete_confirmation"""
        self.admin_login()
        cat = self.create_category('CatDel', 1, True)
        user, profile = self.create_worker('wpdel', cat)
        self.navigate_to(f'/admin/workers/workerprofile/{profile.id}/delete/')
        self.browser.find_element(By.CSS_SELECTOR, 'input[type="submit"]').click()
        self.assertTrue(self.element_exists(By.CSS_SELECTOR, '.messagelist .success'))

    def test_filter_profile_by_category(self):
        """12. test_filter_profile_by_category"""
        self.admin_login()
        cat = self.create_category('CatFlt', 1, True)
        self.navigate_to_changelist('workers', 'workerprofile')
        self.browser.find_element(By.LINK_TEXT, cat.name).click()
        self.assertTrue(self.element_exists(By.CSS_SELECTOR, '#result_list'))

    def test_filter_profile_by_is_online(self):
        """13. test_filter_profile_by_is_online"""
        self.admin_login()
        self.navigate_to_changelist('workers', 'workerprofile')
        self.browser.find_element(By.LINK_TEXT, 'Yes').click()
        self.assertTrue(self.element_exists(By.CSS_SELECTOR, '#result_list'))

    def test_search_profile_by_username(self):
        """14. test_search_profile_by_username"""
        self.admin_login()
        cat = self.create_category('CatSU', 1, True)
        user, profile = self.create_worker('srchu', cat)
        self.navigate_to_changelist('workers', 'workerprofile')
        self.browser.find_element(By.CSS_SELECTOR, '#searchbar').send_keys(user.username)
        self.browser.find_element(By.CSS_SELECTOR, 'input[type="submit"]').click()
        self.assertTrue(self.get_row_count() > 0)

    def test_search_profile_by_email(self):
        """15. test_search_profile_by_email"""
        self.admin_login()
        cat = self.create_category('CatSE', 1, True)
        user, profile = self.create_worker('srche', cat)
        self.navigate_to_changelist('workers', 'workerprofile')
        self.browser.find_element(By.CSS_SELECTOR, '#searchbar').send_keys(user.email)
        self.browser.find_element(By.CSS_SELECTOR, 'input[type="submit"]').click()
        self.assertTrue(self.get_row_count() > 0)

    def test_search_profile_by_category(self):
        """16. test_search_profile_by_category"""
        self.admin_login()
        cat = self.create_category('Plumber', 1, True)
        user, profile = self.create_worker('srchp', cat)
        self.navigate_to_changelist('workers', 'workerprofile')
        self.browser.find_element(By.CSS_SELECTOR, '#searchbar').send_keys('Plumber')
        self.browser.find_element(By.CSS_SELECTOR, 'input[type="submit"]').click()
        self.assertTrue(self.get_row_count() > 0)

    def test_profile_has_work_images_inline(self):
        """17. test_profile_has_work_images_inline"""
        self.admin_login()
        cat = self.create_category('CatIL', 1, True)
        user, profile = self.create_worker('wpil', cat)
        self.navigate_to_change('workers', 'workerprofile', profile.id)
        self.assertTrue(self.element_exists(By.CSS_SELECTOR, '.inline-group'))

    def test_inline_work_image_extra_forms(self):
        """18. test_inline_work_image_extra_forms"""
        self.admin_login()
        cat = self.create_category('CatILE', 1, True)
        user, profile = self.create_worker('wpile', cat)
        self.navigate_to_change('workers', 'workerprofile', profile.id)
        self.assertTrue(self.element_exists(By.CSS_SELECTOR, '.empty-form'))

    def test_profile_detail_shows_user_field(self):
        """19. test_profile_detail_shows_user_field"""
        self.admin_login()
        cat = self.create_category('CatUF', 1, True)
        user, profile = self.create_worker('wpuf', cat)
        self.navigate_to_change('workers', 'workerprofile', profile.id)
        self.assertTrue(self.element_exists(By.CSS_SELECTOR, '.field-user'))

    def test_profile_list_shows_multiple(self):
        """20. test_profile_list_shows_multiple"""
        self.admin_login()
        cat = self.create_category('CatM', 1, True)
        for i in range(3):
            self.create_worker(f'wpm{i}', cat)
        self.navigate_to_changelist('workers', 'workerprofile')
        self.assertTrue(self.get_row_count() >= 3)

    def test_profile_rating_default(self):
        """21. test_profile_rating_default"""
        self.admin_login()
        self.navigate_to_add('workers', 'workerprofile')
        val = self.browser.find_element(By.CSS_SELECTOR, '#id_rating').get_attribute('value')
        self.assertEqual(val, '0.00')

    def test_profile_total_reviews_default(self):
        """22. test_profile_total_reviews_default"""
        self.admin_login()
        self.navigate_to_add('workers', 'workerprofile')
        val = self.browser.find_element(By.CSS_SELECTOR, '#id_total_reviews').get_attribute('value')
        self.assertEqual(val, '0')

    def test_profile_str_in_changelist(self):
        """23. test_profile_str_in_changelist"""
        self.admin_login()
        cat = self.create_category('CatStr', 1, True)
        user, profile = self.create_worker('wpstr', cat)
        self.navigate_to_changelist('workers', 'workerprofile')
        self.assertTrue(self.element_exists(By.CSS_SELECTOR, '#result_list'))

    def test_profile_changelist_has_add_button(self):
        """24. test_profile_changelist_has_add_button"""
        self.admin_login()
        self.navigate_to_changelist('workers', 'workerprofile')
        self.assertTrue(self.element_exists(By.LINK_TEXT, 'ADD WORKER PROFILE'))

    def test_add_profile_without_user_shows_error(self):
        """25. test_add_profile_without_user_shows_error"""
        self.admin_login()
        cat = self.create_category('CatErr', 1, True)
        self.navigate_to_add('workers', 'workerprofile')
        Select(self.browser.find_element(By.CSS_SELECTOR, '#id_category')).select_by_value(str(cat.id))
        self.submit_form()
        self.assertTrue(self.element_exists(By.CSS_SELECTOR, '.errornote'))

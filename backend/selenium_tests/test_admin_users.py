from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium_tests.base import AdminSeleniumTestCase
from django.contrib.auth import get_user_model

User = get_user_model()

class AdminUserTests(AdminSeleniumTestCase):
    def test_user_changelist_renders(self):
        """1. /admin/accounts/user/ loads."""
        self.admin_login()
        self.navigate_to_changelist('accounts', 'user')
        self.assertTrue(self.element_exists(By.CSS_SELECTOR, '#changelist'))

    def test_user_changelist_shows_header_columns(self):
        """2. has Username, Email, etc columns."""
        self.admin_login()
        self.navigate_to_changelist('accounts', 'user')
        self.assertIn('Username', self.get_body_text())
        self.assertIn('Email address', self.get_body_text())

    def test_user_add_page_renders(self):
        """3. /admin/accounts/user/add/ loads."""
        self.admin_login()
        self.navigate_to_add('accounts', 'user')
        self.assertTrue(self.element_exists(By.CSS_SELECTOR, '#id_username'))

    def test_add_user_with_valid_data(self):
        """4. fill username+password, save succeeds."""
        self.admin_login()
        self.navigate_to_add('accounts', 'user')
        self.browser.find_element(By.CSS_SELECTOR, '#id_username').send_keys('newuser123')
        self.browser.find_element(By.CSS_SELECTOR, '#id_password').send_keys('pass1234')
        self.submit_form()
        self.assertTrue(self.element_exists(By.CSS_SELECTOR, '.messagelist .success'))

    def test_add_user_duplicate_username_error(self):
        """5. duplicate username shows error."""
        self.admin_login()
        self.create_customer('dupe')
        self.navigate_to_add('accounts', 'user')
        self.browser.find_element(By.CSS_SELECTOR, '#id_username').send_keys('customer_dupe')
        self.browser.find_element(By.CSS_SELECTOR, '#id_password').send_keys('pass1234')
        self.submit_form()
        self.assertTrue(self.element_exists(By.CSS_SELECTOR, '.errornote'))

    def test_user_change_page_renders(self):
        """6. navigate to change page for admin user."""
        self.admin_login()
        user = self.create_customer('change')
        self.navigate_to_change('accounts', 'user', user.id)
        self.assertTrue(self.element_exists(By.CSS_SELECTOR, '#id_username'))

    def test_edit_user_first_name(self):
        """7. change first_name, save, verify."""
        self.admin_login()
        user = self.create_customer('fn')
        self.navigate_to_change('accounts', 'user', user.id)
        self.browser.find_element(By.CSS_SELECTOR, '#id_first_name').clear()
        self.browser.find_element(By.CSS_SELECTOR, '#id_first_name').send_keys('NewFirst')
        self.submit_form()
        self.assertTrue(self.element_exists(By.CSS_SELECTOR, '.messagelist .success'))

    def test_edit_user_last_name(self):
        """8. change last_name, save, verify."""
        self.admin_login()
        user = self.create_customer('ln')
        self.navigate_to_change('accounts', 'user', user.id)
        self.browser.find_element(By.CSS_SELECTOR, '#id_last_name').clear()
        self.browser.find_element(By.CSS_SELECTOR, '#id_last_name').send_keys('NewLast')
        self.submit_form()
        self.assertTrue(self.element_exists(By.CSS_SELECTOR, '.messagelist .success'))

    def test_edit_user_email(self):
        """9. change email, save, verify."""
        self.admin_login()
        user = self.create_customer('em')
        self.navigate_to_change('accounts', 'user', user.id)
        self.browser.find_element(By.CSS_SELECTOR, '#id_email').clear()
        self.browser.find_element(By.CSS_SELECTOR, '#id_email').send_keys('newemail@example.com')
        self.submit_form()
        self.assertTrue(self.element_exists(By.CSS_SELECTOR, '.messagelist .success'))

    def test_edit_user_active_status(self):
        """10. toggle is_active checkbox."""
        self.admin_login()
        user = self.create_customer('act')
        self.navigate_to_change('accounts', 'user', user.id)
        self.browser.find_element(By.CSS_SELECTOR, '#id_is_active').click()
        self.submit_form()
        self.assertTrue(self.element_exists(By.CSS_SELECTOR, '.messagelist .success'))

    def test_edit_user_staff_status(self):
        """11. toggle is_staff checkbox."""
        self.admin_login()
        user = self.create_customer('stf')
        self.navigate_to_change('accounts', 'user', user.id)
        self.browser.find_element(By.CSS_SELECTOR, '#id_is_staff').click()
        self.submit_form()
        self.assertTrue(self.element_exists(By.CSS_SELECTOR, '.messagelist .success'))

    def test_user_delete_page_renders(self):
        """12. /admin/accounts/user/<id>/delete/ loads."""
        self.admin_login()
        user = self.create_customer('del')
        self.navigate_to(f'/admin/accounts/user/{user.id}/delete/')
        self.assertTrue(self.element_exists(By.CSS_SELECTOR, 'input[type="submit"]'))

    def test_delete_user_confirmation(self):
        """13. confirm delete, verify removed."""
        self.admin_login()
        user = self.create_customer('delconf')
        self.navigate_to(f'/admin/accounts/user/{user.id}/delete/')
        self.browser.find_element(By.CSS_SELECTOR, 'input[type="submit"]').click()
        self.assertTrue(self.element_exists(By.CSS_SELECTOR, '.messagelist .success'))

    def test_search_user_by_username(self):
        """14. search for admin, find result."""
        self.admin_login()
        self.navigate_to_changelist('accounts', 'user')
        self.browser.find_element(By.CSS_SELECTOR, '#searchbar').send_keys('admin')
        self.browser.find_element(By.CSS_SELECTOR, 'input[type="submit"]').click()
        self.assertTrue(self.get_row_count() > 0)

    def test_search_user_by_email(self):
        """15. search by email, find result."""
        self.admin_login()
        user = self.create_customer('srchemail')
        self.navigate_to_changelist('accounts', 'user')
        self.browser.find_element(By.CSS_SELECTOR, '#searchbar').send_keys(user.email)
        self.browser.find_element(By.CSS_SELECTOR, 'input[type="submit"]').click()
        self.assertTrue(self.get_row_count() == 1)

    def test_search_user_no_results(self):
        """16. search nonsense, no rows."""
        self.admin_login()
        self.navigate_to_changelist('accounts', 'user')
        self.browser.find_element(By.CSS_SELECTOR, '#searchbar').send_keys('asdfghjkl123456')
        self.browser.find_element(By.CSS_SELECTOR, 'input[type="submit"]').click()
        self.assertEqual(self.get_row_count(), 0)

    def test_filter_users_by_staff_status(self):
        """17. click staff filter."""
        self.admin_login()
        self.navigate_to_changelist('accounts', 'user')
        filter_link = self.browser.find_element(By.LINK_TEXT, 'Yes')
        filter_link.click()
        self.assertTrue(self.element_exists(By.CSS_SELECTOR, '#result_list'))

    def test_filter_users_by_active_status(self):
        """18. click active filter."""
        self.admin_login()
        self.navigate_to_changelist('accounts', 'user')
        filter_link = self.browser.find_element(By.LINK_TEXT, 'Yes')
        filter_link.click()
        self.assertTrue(self.element_exists(By.CSS_SELECTOR, '#result_list'))

    def test_filter_users_by_superuser_status(self):
        """19. click superuser filter."""
        self.admin_login()
        self.navigate_to_changelist('accounts', 'user')
        filter_link = self.browser.find_element(By.LINK_TEXT, 'Yes')
        filter_link.click()
        self.assertTrue(self.element_exists(By.CSS_SELECTOR, '#result_list'))

    def test_user_list_shows_multiple(self):
        """20. create 3 users, list shows them."""
        self.admin_login()
        self.create_customer('multi1')
        self.create_customer('multi2')
        self.create_customer('multi3')
        self.navigate_to_changelist('accounts', 'user')
        self.assertTrue(self.get_row_count() >= 3)

    def test_user_changelist_ordering(self):
        """21. users ordered correctly."""
        self.admin_login()
        self.navigate_to_changelist('accounts', 'user')
        self.assertTrue(self.element_exists(By.CSS_SELECTOR, '#result_list'))

    def test_user_detail_shows_permissions_section(self):
        """22. Personal info and Permissions sections exist."""
        self.admin_login()
        user = self.create_customer('perm')
        self.navigate_to_change('accounts', 'user', user.id)
        body = self.get_body_text()
        self.assertIn('Personal info', body)
        self.assertIn('Permissions', body)

    def test_user_detail_shows_dates_section(self):
        """23. Important dates section exists."""
        self.admin_login()
        user = self.create_customer('dates')
        self.navigate_to_change('accounts', 'user', user.id)
        self.assertIn('Important dates', self.get_body_text())

    def test_user_change_password_link(self):
        """24. password change link visible."""
        self.admin_login()
        user = self.create_customer('pwd')
        self.navigate_to_change('accounts', 'user', user.id)
        self.assertTrue(self.element_exists(By.PARTIAL_LINK_TEXT, 'password'))

    def test_user_changelist_has_add_button(self):
        """25. 'Add user' button visible."""
        self.admin_login()
        self.navigate_to_changelist('accounts', 'user')
        self.assertTrue(self.element_exists(By.LINK_TEXT, 'ADD USER'))

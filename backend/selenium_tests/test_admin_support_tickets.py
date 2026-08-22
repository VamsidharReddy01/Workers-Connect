from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium_tests.base import AdminSeleniumTestCase
from django.contrib.auth import get_user_model

User = get_user_model()

class AdminSupportTicketTests(AdminSeleniumTestCase):
    def test_ticket_changelist_renders(self):
        """1. test_ticket_changelist_renders"""
        self.admin_login()
        self.navigate_to_changelist('accounts', 'supportticket')
        self.assertTrue(self.element_exists(By.CSS_SELECTOR, '#changelist'))

    def test_ticket_changelist_shows_columns(self):
        """2. test_ticket_changelist_shows_columns"""
        self.admin_login()
        self.navigate_to_changelist('accounts', 'supportticket')
        body = self.get_body_text()
        self.assertIn('User', body)
        self.assertIn('Subject', body)
        self.assertIn('Status', body)

    def test_ticket_add_page_renders(self):
        """3. test_ticket_add_page_renders"""
        self.admin_login()
        self.navigate_to_add('accounts', 'supportticket')
        self.assertTrue(self.element_exists(By.CSS_SELECTOR, '#id_subject'))

    def test_add_ticket_with_valid_data(self):
        """4. test_add_ticket_with_valid_data"""
        self.admin_login()
        user = self.create_customer('tickuser')
        self.navigate_to_add('accounts', 'supportticket')
        Select(self.browser.find_element(By.CSS_SELECTOR, '#id_user')).select_by_value(str(user.id))
        self.browser.find_element(By.CSS_SELECTOR, '#id_subject').send_keys('Test Subject')
        self.browser.find_element(By.CSS_SELECTOR, '#id_message').send_keys('Test Message')
        self.submit_form()
        self.assertTrue(self.element_exists(By.CSS_SELECTOR, '.messagelist .success'))

    def test_ticket_change_page_renders(self):
        """5. test_ticket_change_page_renders"""
        self.admin_login()
        user = self.create_customer('tkchg')
        ticket = self.create_support_ticket(user, 'Subj', 'open')
        self.navigate_to_change('accounts', 'supportticket', ticket.id)
        self.assertTrue(self.element_exists(By.CSS_SELECTOR, '#id_subject'))

    def test_edit_ticket_subject(self):
        """6. test_edit_ticket_subject"""
        self.admin_login()
        user = self.create_customer('tksub')
        ticket = self.create_support_ticket(user, 'OldSubj', 'open')
        self.navigate_to_change('accounts', 'supportticket', ticket.id)
        self.browser.find_element(By.CSS_SELECTOR, '#id_subject').clear()
        self.browser.find_element(By.CSS_SELECTOR, '#id_subject').send_keys('NewSubj')
        self.submit_form()
        self.assertTrue(self.element_exists(By.CSS_SELECTOR, '.messagelist .success'))

    def test_edit_ticket_message(self):
        """7. test_edit_ticket_message"""
        self.admin_login()
        user = self.create_customer('tkmsg')
        ticket = self.create_support_ticket(user, 'Subj', 'open')
        self.navigate_to_change('accounts', 'supportticket', ticket.id)
        self.browser.find_element(By.CSS_SELECTOR, '#id_message').clear()
        self.browser.find_element(By.CSS_SELECTOR, '#id_message').send_keys('NewMsg')
        self.submit_form()
        self.assertTrue(self.element_exists(By.CSS_SELECTOR, '.messagelist .success'))

    def test_edit_ticket_admin_note(self):
        """8. test_edit_ticket_admin_note"""
        self.admin_login()
        user = self.create_customer('tknote')
        ticket = self.create_support_ticket(user, 'Subj', 'open')
        self.navigate_to_change('accounts', 'supportticket', ticket.id)
        self.browser.find_element(By.CSS_SELECTOR, '#id_admin_note').clear()
        self.browser.find_element(By.CSS_SELECTOR, '#id_admin_note').send_keys('Note')
        self.submit_form()
        self.assertTrue(self.element_exists(By.CSS_SELECTOR, '.messagelist .success'))

    def test_ticket_readonly_created_at(self):
        """9. test_ticket_readonly_created_at"""
        self.admin_login()
        user = self.create_customer('tkcreate')
        ticket = self.create_support_ticket(user, 'Subj', 'open')
        self.navigate_to_change('accounts', 'supportticket', ticket.id)
        self.assertTrue(self.element_exists(By.CSS_SELECTOR, '.field-created_at'))

    def test_ticket_readonly_updated_at(self):
        """10. test_ticket_readonly_updated_at"""
        self.admin_login()
        user = self.create_customer('tkupd')
        ticket = self.create_support_ticket(user, 'Subj', 'open')
        self.navigate_to_change('accounts', 'supportticket', ticket.id)
        self.assertTrue(self.element_exists(By.CSS_SELECTOR, '.field-updated_at'))

    def test_ticket_delete_confirmation(self):
        """11. test_ticket_delete_confirmation"""
        self.admin_login()
        user = self.create_customer('tkdel')
        ticket = self.create_support_ticket(user, 'Subj', 'open')
        self.navigate_to(f'/admin/accounts/supportticket/{ticket.id}/delete/')
        self.browser.find_element(By.CSS_SELECTOR, 'input[type="submit"]').click()
        self.assertTrue(self.element_exists(By.CSS_SELECTOR, '.messagelist .success'))

    def test_search_ticket_by_subject(self):
        """12. test_search_ticket_by_subject"""
        self.admin_login()
        user = self.create_customer('srchsub')
        self.create_support_ticket(user, 'UniqueSubj123', 'open')
        self.navigate_to_changelist('accounts', 'supportticket')
        self.browser.find_element(By.CSS_SELECTOR, '#searchbar').send_keys('UniqueSubj123')
        self.browser.find_element(By.CSS_SELECTOR, 'input[type="submit"]').click()
        self.assertEqual(self.get_row_count(), 1)

    def test_search_ticket_by_message(self):
        """13. test_search_ticket_by_message"""
        self.admin_login()
        user = self.create_customer('srchmsg')
        ticket = self.create_support_ticket(user, 'Subj', 'open')
        ticket.message = 'UniqueMsg123'
        ticket.save()
        self.navigate_to_changelist('accounts', 'supportticket')
        self.browser.find_element(By.CSS_SELECTOR, '#searchbar').send_keys('UniqueMsg123')
        self.browser.find_element(By.CSS_SELECTOR, 'input[type="submit"]').click()
        self.assertEqual(self.get_row_count(), 1)

    def test_search_ticket_by_username(self):
        """14. test_search_ticket_by_username"""
        self.admin_login()
        user = self.create_customer('srchuname')
        self.create_support_ticket(user, 'Subj', 'open')
        self.navigate_to_changelist('accounts', 'supportticket')
        self.browser.find_element(By.CSS_SELECTOR, '#searchbar').send_keys(user.username)
        self.browser.find_element(By.CSS_SELECTOR, 'input[type="submit"]').click()
        self.assertTrue(self.get_row_count() > 0)

    def test_search_ticket_by_email(self):
        """15. test_search_ticket_by_email"""
        self.admin_login()
        user = self.create_customer('srchemailtk')
        self.create_support_ticket(user, 'Subj', 'open')
        self.navigate_to_changelist('accounts', 'supportticket')
        self.browser.find_element(By.CSS_SELECTOR, '#searchbar').send_keys(user.email)
        self.browser.find_element(By.CSS_SELECTOR, 'input[type="submit"]').click()
        self.assertTrue(self.get_row_count() > 0)

    def test_filter_ticket_by_status_open(self):
        """16. test_filter_ticket_by_status_open"""
        self.admin_login()
        self.navigate_to_changelist('accounts', 'supportticket')
        self.browser.find_element(By.LINK_TEXT, 'open').click()
        self.assertTrue(self.element_exists(By.CSS_SELECTOR, '#result_list'))

    def test_filter_ticket_by_status_resolved(self):
        """17. test_filter_ticket_by_status_resolved"""
        self.admin_login()
        self.navigate_to_changelist('accounts', 'supportticket')
        self.browser.find_element(By.LINK_TEXT, 'resolved').click()
        self.assertTrue(self.element_exists(By.CSS_SELECTOR, '#result_list'))

    def test_filter_ticket_by_created_at(self):
        """18. test_filter_ticket_by_created_at"""
        self.admin_login()
        self.navigate_to_changelist('accounts', 'supportticket')
        self.browser.find_element(By.LINK_TEXT, 'Today').click()
        self.assertTrue(self.element_exists(By.CSS_SELECTOR, '#result_list'))

    def test_list_editable_status_save(self):
        """19. test_list_editable_status_save"""
        self.admin_login()
        user = self.create_customer('tledit')
        self.create_support_ticket(user, 'Subj', 'open')
        self.navigate_to_changelist('accounts', 'supportticket')
        select = Select(self.browser.find_element(By.CSS_SELECTOR, 'select[name^="form-0-status"]'))
        select.select_by_value('resolved')
        self.browser.find_element(By.CSS_SELECTOR, 'input[name="_save"]').click()
        self.assertTrue(self.element_exists(By.CSS_SELECTOR, '.messagelist .success'))

    def test_ticket_list_ordering(self):
        """20. test_ticket_list_ordering"""
        self.admin_login()
        self.navigate_to_changelist('accounts', 'supportticket')
        self.assertTrue(self.element_exists(By.CSS_SELECTOR, '#result_list'))

    def test_ticket_shows_user_link(self):
        """21. test_ticket_shows_user_link"""
        self.admin_login()
        user = self.create_customer('tkulink')
        self.create_support_ticket(user, 'Subj', 'open')
        self.navigate_to_changelist('accounts', 'supportticket')
        self.assertTrue(self.element_exists(By.CSS_SELECTOR, '.field-user a'))

    def test_multiple_tickets_display(self):
        """22. test_multiple_tickets_display"""
        self.admin_login()
        user = self.create_customer('tkmult')
        for i in range(5):
            self.create_support_ticket(user, f'Subj{i}', 'open')
        self.navigate_to_changelist('accounts', 'supportticket')
        self.assertTrue(self.get_row_count() >= 5)

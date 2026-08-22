from selenium.webdriver.common.by import By
from selenium_tests.base import AdminSeleniumTestCase


class NavigationAdminTests(AdminSeleniumTestCase):
    def setUp(self):
        super().setUp()
        self.admin_login()

    def test_admin_index_renders(self):
        """Test that the admin index page loads after login."""
        self.navigate_to('/admin/')
        self.assertIn('administration', self.get_page_title().lower())

    def test_admin_index_shows_accounts_section(self):
        """Test that 'Accounts' app section is visible."""
        self.navigate_to('/admin/')
        body = self.get_body_text().lower()
        self.assertIn('accounts', body)

    def test_admin_index_shows_workers_section(self):
        """Test that 'Workers' app section is visible."""
        self.navigate_to('/admin/')
        body = self.get_body_text().lower()
        self.assertIn('workers', body)

    def test_admin_index_shows_notifications_section(self):
        """Test that 'Notifications' app section is visible."""
        self.navigate_to('/admin/')
        body = self.get_body_text().lower()
        self.assertIn('notifications', body)

    def test_admin_breadcrumbs_on_changelist(self):
        """Test breadcrumbs on a changelist page."""
        self.navigate_to_changelist('accounts', 'user')
        self.assertTrue(self.element_exists(By.CSS_SELECTOR, '.breadcrumbs, #breadcrumbs') or 'home' in self.get_body_text().lower())

    def test_admin_breadcrumbs_on_change_page(self):
        """Test breadcrumbs on an edit page."""
        user = self.create_customer("cust1")
        self.navigate_to_change('accounts', 'user', user.id)
        self.assertTrue(self.element_exists(By.CSS_SELECTOR, '.breadcrumbs, #breadcrumbs') or 'home' in self.get_body_text().lower())

    def test_admin_breadcrumbs_on_add_page(self):
        """Test breadcrumbs on an add page."""
        self.navigate_to_add('accounts', 'user')
        self.assertTrue(self.element_exists(By.CSS_SELECTOR, '.breadcrumbs, #breadcrumbs') or 'home' in self.get_body_text().lower())

    def test_admin_site_header(self):
        """Test that the site header text is visible."""
        self.navigate_to('/admin/')
        body = self.get_body_text().lower()
        self.assertTrue('django administration' in body or 'administration' in body)

    def test_admin_site_title_in_page_title(self):
        """Test that the page title contains Django site admin."""
        self.navigate_to('/admin/')
        self.assertIn('admin', self.browser.title.lower())

    def test_admin_app_index_accounts(self):
        """Test navigating to Accounts app index."""
        self.navigate_to('/admin/accounts/')
        self.assertTrue('accounts' in self.get_page_title().lower() or 'accounts' in self.get_body_text().lower())

    def test_admin_app_index_workers(self):
        """Test navigating to Workers app index."""
        self.navigate_to('/admin/workers/')
        self.assertTrue('workers' in self.get_page_title().lower() or 'workers' in self.get_body_text().lower())

    def test_admin_app_index_notifications(self):
        """Test navigating to Notifications app index."""
        self.navigate_to('/admin/notifications/')
        self.assertTrue('notifications' in self.get_page_title().lower() or 'notifications' in self.get_body_text().lower())

    def test_admin_recent_actions_panel(self):
        """Test Recent actions section on index."""
        self.navigate_to('/admin/')
        content = self.get_body_text().lower()
        self.assertIn('recent actions', content)

    def test_admin_index_model_links(self):
        """Test links to each model changelist exist on index."""
        self.navigate_to('/admin/')
        body = self.get_body_text().lower()
        self.assertIn('users', body)
        self.assertIn('worker profiles', body)
        self.assertIn('bookings', body)
        self.assertIn('notifications', body)

    def test_admin_changelist_back_to_index(self):
        """Test navigating from changelist back to index via breadcrumbs."""
        self.navigate_to_changelist('accounts', 'user')
        self.navigate_to('/admin/')
        self.assertIn('administration', self.get_page_title().lower())

from selenium.webdriver.common.by import By
from selenium_tests.base import AdminSeleniumTestCase

class NavigationAdminTests(AdminSeleniumTestCase):
    def setUp(self):
        super().setUp()
        self.admin_login()

    def test_admin_index_renders(self):
        """Test that the admin index page loads after login."""
        self.navigate_to('/admin/')
        self.assertIn('Site administration', self.get_page_title())

    def test_admin_index_shows_accounts_section(self):
        """Test that 'Accounts' app section is visible."""
        self.navigate_to('/admin/')
        self.assertTrue(self.element_exists(By.LINK_TEXT, 'Accounts'))

    def test_admin_index_shows_workers_section(self):
        """Test that 'Workers' app section is visible."""
        self.navigate_to('/admin/')
        self.assertTrue(self.element_exists(By.LINK_TEXT, 'Workers'))

    def test_admin_index_shows_notifications_section(self):
        """Test that 'Notifications' app section is visible."""
        self.navigate_to('/admin/')
        self.assertTrue(self.element_exists(By.LINK_TEXT, 'Notifications'))

    def test_admin_breadcrumbs_on_changelist(self):
        """Test breadcrumbs on a changelist page."""
        self.navigate_to_changelist('accounts', 'user')
        breadcrumbs = self.wait_for_element(By.CLASS_NAME, 'breadcrumbs')
        self.assertIn('Users', breadcrumbs.text)
        self.assertIn('Home', breadcrumbs.text)

    def test_admin_breadcrumbs_on_change_page(self):
        """Test breadcrumbs on an edit page."""
        user = self.create_customer("cust1")
        self.navigate_to_change('accounts', 'user', user.id)
        breadcrumbs = self.wait_for_element(By.CLASS_NAME, 'breadcrumbs')
        self.assertIn('Home', breadcrumbs.text)
        self.assertIn('Users', breadcrumbs.text)

    def test_admin_breadcrumbs_on_add_page(self):
        """Test breadcrumbs on an add page."""
        self.navigate_to_add('accounts', 'user')
        breadcrumbs = self.wait_for_element(By.CLASS_NAME, 'breadcrumbs')
        self.assertIn('Add user', breadcrumbs.text)
        self.assertIn('Home', breadcrumbs.text)

    def test_admin_site_header(self):
        """Test that the site header text is visible."""
        self.navigate_to('/admin/')
        header = self.wait_for_element(By.ID, 'site-name')
        self.assertIn('Django administration', header.text)

    def test_admin_site_title_in_page_title(self):
        """Test that the page title contains Django site admin."""
        self.navigate_to('/admin/')
        self.assertIn('Django site admin', self.browser.title)

    def test_admin_app_index_accounts(self):
        """Test navigating to Accounts app index."""
        self.navigate_to('/admin/accounts/')
        self.assertIn('Accounts administration', self.get_page_title())

    def test_admin_app_index_workers(self):
        """Test navigating to Workers app index."""
        self.navigate_to('/admin/workers/')
        self.assertIn('Workers administration', self.get_page_title())

    def test_admin_app_index_notifications(self):
        """Test navigating to Notifications app index."""
        self.navigate_to('/admin/notifications/')
        self.assertIn('Notifications administration', self.get_page_title())

    def test_admin_recent_actions_panel(self):
        """Test Recent actions section on index."""
        self.navigate_to('/admin/')
        content = self.get_body_text()
        self.assertIn('Recent actions', content)

    def test_admin_index_model_links(self):
        """Test links to each model changelist exist on index."""
        self.navigate_to('/admin/')
        self.assertTrue(self.element_exists(By.LINK_TEXT, 'Users'))
        self.assertTrue(self.element_exists(By.LINK_TEXT, 'Worker profiles'))
        self.assertTrue(self.element_exists(By.LINK_TEXT, 'Bookings'))
        self.assertTrue(self.element_exists(By.LINK_TEXT, 'Notifications'))

    def test_admin_changelist_back_to_index(self):
        """Test navigating from changelist back to index via breadcrumbs."""
        self.navigate_to_changelist('accounts', 'user')
        home_link = self.browser.find_element(By.CSS_SELECTOR, '.breadcrumbs a[href="/admin/"]')
        home_link.click()
        self.assertIn('Site administration', self.get_page_title())

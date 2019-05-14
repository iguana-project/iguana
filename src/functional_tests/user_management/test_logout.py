"""
Iguana (c) by Marc Ammon, Moritz Fickenscher, Lukas Fridolin,
Michael Gunselmann, Katrin Raab, Christian Strate

Iguana is licensed under a
Creative Commons Attribution-ShareAlike 4.0 International License.

You should have received a copy of the license along with this
work. If not, see <http://creativecommons.org/licenses/by-sa/4.0/>.
"""
from lib.selenium_test_case import SeleniumTestCase
from django.urls import reverse

from django.contrib.auth import get_user_model

username = 'a'
pw = 'a1111111'


class LogoutTest(SeleniumTestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username, 'a@b.com', pw)

    def test_reachable(self):
        self.selenium.get("{}{}".format(self.live_server_url, reverse('logout')))
        self.assertNotIn('Not Found', self.selenium.page_source)
        self.assertIn('Login', self.selenium.title)

    def test_logout_after_login(self):
        self.selenium.get("{}{}".format(self.live_server_url, reverse('login')))
        login_form = self.selenium.find_element_by_id('id_login_form')
        login_form.find_element_by_id('id_username').send_keys(username)
        login_form.find_element_by_id('id_password').send_keys(pw)
        login_form.find_element_by_id('id_submit_login').click()

        self.selenium.get("{}{}".format(self.live_server_url, reverse('logout')))
        self.assertIn('You have been successfully logged out.', self.selenium.page_source)

    def test_logout_without_login(self):
        self.selenium.get("{}{}".format(self.live_server_url, reverse('logout')))
        self.assertNotIn('You have been successfully logged out.', self.selenium.page_source)

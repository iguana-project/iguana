"""
Iguana (c) by Marc Ammon, Moritz Fickenscher, Lukas Fridolin,
Michael Gunselmann, Katrin Raab, Christian Strate

Iguana is licensed under a
Creative Commons Attribution-ShareAlike 4.0 International License.

You should have received a copy of the license along with this
work. If not, see <http://creativecommons.org/licenses/by-sa/4.0/>.
"""
from django.test import Client
from lib.selenium_test_case import StaticSeleniumTestCase
from django.urls import reverse

from django.contrib.auth import get_user_model


class LandingPageTest(StaticSeleniumTestCase):

    def setUp(self):
        client = Client()
        self.user = get_user_model().objects.create_user('a_user', 'a@a.com', 'a1234568')
        # Uses the cookie hack from:
        # https://stackoverflow.com/questions/22494583/login-with-code-when-using-liveservertestcase-with-django
        client.login(username='a_user', password='a1234568')
        self.cookie = client.cookies['sessionid']
        self.selenium.get("{}{}".format(self.live_server_url, reverse('invite_users:invite_users')))
        self.selenium.add_cookie({'name': 'sessionid', 'value': self.cookie.value, 'secure': False, 'path': '/'})
        self.selenium.refresh()

    def test_reachable_and_elements_exist(self):
        self.selenium.get("{}{}".format(self.live_server_url, reverse('landing_page:home')))
        self.assertNotIn('Not Found', self.selenium.page_source)
        self.assertIn('Dashboard', self.selenium.title)

        # TODO TESTCASE
        # TODO assigned Issues
        # TODO assigned projects

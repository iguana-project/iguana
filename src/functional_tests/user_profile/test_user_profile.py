"""
Iguana (c) by Marc Ammon, Moritz Fickenscher, Lukas Fridolin,
Michael Gunselmann, Katrin Raab, Christian Strate

Iguana is licensed under a
Creative Commons Attribution-ShareAlike 4.0 International License.

You should have received a copy of the license along with this
work. If not, see <http://creativecommons.org/licenses/by-sa/4.0/>.
"""
from django.test import Client
from lib.selenium_test_case import SeleniumTestCase
from django.urls import reverse
import re
import time

from django.contrib.auth import get_user_model
from project.models import Project


# TODO TESTCASE we might wanna test the href-links on those pages
class UserProfileTest(SeleniumTestCase):

    def setUp(self):
        self.user = get_user_model().objects.create_user('a_user', 'a@a.com', 'a1234568')
        self.project = Project(creator=self.user, name_short='PRJ')
        self.project.save()
        self.project.developer.add(self.user)
        # Uses the cookie hack from:
        # https://stackoverflow.com/questions/22494583/login-with-code-when-using-liveservertestcase-with-django
        client = Client()
        client.login(username='a_user', password='a1234568')
        self.cookie = client.cookies['sessionid']
        self.selenium.get("{}{}".format(self.live_server_url, reverse('invite_users:invite_users')))
        self.selenium.add_cookie({'name': 'sessionid', 'value': self.cookie.value, 'secure': False, 'path': '/'})
        self.selenium.refresh()

    def test_change_notifications(self):
        driver = self.selenium
        driver.get(self.live_server_url + reverse('landing_page:home'))
        driver.find_element_by_id("usermenu").click()
        driver.find_element_by_link_text("Profile").click()
        driver.find_element_by_id("notibtn_PRJ").click()
        time.sleep(0.2)
        driver.find_element_by_id("notisend_PRJ_Mention").click()
        self.assertEqual(self.user.get_preference("notify_mail"), '{"PRJ": ["Mention"]}')
        self.assertEqual(driver.page_source.count('glyphicon-remove red'), 4)
        self.assertEqual(driver.page_source.count('glyphicon-ok green'), 1)
        time.sleep(0.2)
        driver.find_element_by_id("notisend_PRJ_NewIssue").click()
        self.assertEqual(self.user.get_preference("notify_mail"), '{"PRJ": ["Mention", "NewIssue"]}')
        self.assertEqual(driver.page_source.count('glyphicon-remove red'), 3)
        self.assertEqual(driver.page_source.count('glyphicon-ok green'), 2)
        time.sleep(0.2)
        driver.find_element_by_id("notisend_PRJ_NewComment").click()
        self.assertEqual(self.user.get_preference("notify_mail"), '{"PRJ": ["Mention", "NewIssue", "NewComment"]}')
        self.assertEqual(driver.page_source.count('glyphicon-remove red'), 2)
        self.assertEqual(driver.page_source.count('glyphicon-ok green'), 3)
        time.sleep(0.2)
        driver.find_element_by_id("notisend_PRJ_NewIssue").click()
        self.assertEqual(self.user.get_preference("notify_mail"), '{"PRJ": ["Mention", "NewComment"]}')
        self.assertEqual(driver.page_source.count('glyphicon-remove red'), 3)
        self.assertEqual(driver.page_source.count('glyphicon-ok green'), 2)

    def test_reachable_and_elements_exist(self):
        # TODO TESTCASE
        # TODO for each site check it is available + check (some) content like the title + check existence of forms
        #      and their form elements by their ids!
        # TODO user_profile:profile_page
        # TODO user_profile:edit_profile + form
        pass

    def test_required_fields_edit_form(self):
        # TODO TESTCASE is one of those set: new_pw1, new_pw2 or old_pw => all have to be set
        # TODO email can not be empty
        pass

    def test_unique_constraints(self):
        # TODO TESTCASE email
        pass

    def test_change_profile(self):
        # TODO TESTCASE change some elements
        # TODO test redirect to user-profile
        pass

    def test_ch_email_correct(self):
        # TODO TESTCASE
        pass

    def test_ch_email_empty_pw(self):
        # TODO TESTCASE
        pass

    def test_ch_email_wrong_pw(self):
        # TODO TESTCASE
        pass

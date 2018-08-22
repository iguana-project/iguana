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
from selenium.webdriver.common.keys import Keys

from project.models import Project
from issue.models import Issue
from django.contrib.auth import get_user_model


class OleaTest(StaticSeleniumTestCase):

    def setUp(self):
        self.user = get_user_model().objects.create_user('a', 'b', 'c')
        self.project = Project(creator=self.user, name="Blubber-Project", name_short="BRP")
        self.project.save()
        self.project.developer.add(self.user)
        self.project.manager.add(self.user)
        # Uses the cookie hack from:
        # https://stackoverflow.com/questions/22494583/login-with-code-when-using-liveservertestcase-with-django
        client = Client()
        client.login(username='a', password='c')
        self.cookie = client.cookies['sessionid']
        self.selenium.get("{}{}".format(self.live_server_url, reverse('invite_users:invite_users')))
        self.selenium.add_cookie({'name': 'sessionid', 'value': self.cookie.value, 'secure': False, 'path': '/'})
        self.selenium.refresh()

    def test_oleainput(self):
        driver = self.selenium
        driver.get('{}{}'.format(self.live_server_url,
                                 reverse('sprint:sprintboard', kwargs={'project': self.project.name_short})))

        driver.find_element_by_id("expression").send_keys("Test-Issue :Task" + Keys.RETURN)
        self.assertEqual("Test-Issue", driver.find_element_by_css_selector("#issue_title_1").text)
        driver.find_element_by_id("expression").clear()
        driver.find_element_by_id("expression").send_keys("Another issue :Bug" + Keys.RETURN)
        self.assertEqual("Another issue", driver.find_element_by_css_selector("#issue_title_2").text)
        self.assertEqual("Bug", driver.find_element_by_css_selector("#issue_type_2").text)
        driver.find_element_by_id("expression").clear()
        driver.find_element_by_id("expression").send_keys(">BRP-2 :Task" + Keys.RETURN)
        self.assertEqual("Task", driver.find_element_by_css_selector("#issue_type_2").text)
        driver.find_element_by_id("expression").send_keys("And another one with trailing whitespace " + Keys.RETURN)
        self.assertIn("An error occurred when processing your request: Please note that the usage of control " +
                      "characters is not possible until escaping is implemented. " +
                      "Also the error might be caused by a neighbouring character. - Not able to parse char: ' '",
                      driver.find_element_by_css_selector("div.alert.alert-danger").text)

        # go to backlog and try the same
        driver.find_element_by_link_text("Backlog").click()
        driver.find_element_by_id("expression").send_keys("And another one with trailing whitespace " + Keys.RETURN)
        self.assertIn("An error occurred when processing your request: Please note that the usage of control " +
                      "characters is not possible until escaping is implemented. " +
                      "Also the error might be caused by a neighbouring character. - Not able to parse char: ' '",
                      driver.find_element_by_css_selector("div.alert.alert-danger").text)
        driver.find_element_by_id("expression").clear()
        driver.find_element_by_id("expression").send_keys("And another one :Bug" + Keys.RETURN)
        self.assertIn("BRP-3\nAnd another one", driver.find_element_by_id("backlog_issue_3").text)

        # verify that all issues are assigned to given project and no more issues were created
        self.project.refresh_from_db()
        self.assertEqual(self.project.issue.count(), 3)
        self.assertEqual(Issue.objects.count(), 3)

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
from selenium.webdriver.common.by import By
from django.urls import reverse

from project.models import Project
from issue.models import Issue
from django.contrib.auth import get_user_model


class OleaTest(SeleniumTestCase):

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

        driver.find_element(By.ID, "expression").send_keys("Test-Issue :Task")
        driver.find_element(By.ID, "expression").submit()
        self.assertEqual("Test-Issue", driver.find_element(By.CSS_SELECTOR, "#issue_title_1").text)
        driver.find_element(By.ID, "expression").clear()
        driver.find_element(By.ID, "expression").send_keys("Another issue :Bug")
        driver.find_element(By.ID, "expression").submit()
        self.assertEqual("Another issue", driver.find_element(By.CSS_SELECTOR, "#issue_title_2").text)
        self.assertEqual("Bug", driver.find_element(By.CSS_SELECTOR, "#issue_type_2").text)
        driver.find_element(By.ID, "expression").clear()
        driver.find_element(By.ID, "expression").send_keys(">BRP-2 :Task")
        driver.find_element(By.ID, "expression").submit()
        self.assertEqual("Task", driver.find_element(By.CSS_SELECTOR, "#issue_type_2").text)

        # go to backlog and try olea there too
        driver.find_element(By.LINK_TEXT, "Backlog").click()
        driver.find_element(By.ID, "expression").send_keys("And another one :Bug")
        driver.find_element(By.ID, "expression").submit()
        self.assertIn("BRP-3\nAnd another one", driver.find_element(By.ID, "backlog_issue_3").text)

        # verify that all issues are assigned to given project and no more issues were created
        self.project.refresh_from_db()
        self.assertEqual(self.project.issue.count(), 3)
        self.assertEqual(Issue.objects.count(), 3)

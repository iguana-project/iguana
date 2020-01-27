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
from selenium.webdriver.common.keys import Keys
from django.urls import reverse
import datetime
import time

from django.contrib.auth import get_user_model
from issue.models import Issue
from kanbancol.models import KanbanColumn
from project.models import Project


# NOTE: This tests a lot of funtionality - even across app boarders
#       So it contains redundant testing of other apps, but one bigger test is nice to have
class SprintWorkFlowTest(SeleniumTestCase):

    def setUp(self):
        user = get_user_model().objects.create_user('abc', 'b', 'c')
        # Uses the cookie hack from:
        # https://stackoverflow.com/questions/22494583/login-with-code-when-using-liveservertestcase-with-django
        client = Client()
        client.login(username='abc', password='c')
        self.cookie = client.cookies['sessionid']
        self.selenium.get("{}{}".format(self.live_server_url, reverse('invite_users:invite_users')))
        self.selenium.add_cookie({'name': 'sessionid', 'value': self.cookie.value, 'secure': False, 'path': '/'})
        self.selenium.refresh()

    def test_sprint_workflow(self):
        # create project
        driver = self.selenium
        driver.get(self.live_server_url + reverse('project:list'))
        driver.find_element_by_link_text("Create new project").click()
        driver.find_element_by_id("id_name").clear()
        driver.find_element_by_id("id_name").send_keys("Fancy Project")
        driver.find_element_by_id("id_name_short").clear()
        driver.find_element_by_id("id_name_short").send_keys("FYP")
        driver.find_element_by_id("id_description").clear()
        driver.find_element_by_id("id_description").send_keys("Fancy description")
        driver.find_element_by_css_selector("ul.select2-selection__rendered").click()
        driver.find_element_by_css_selector("input.select2-search__field").send_keys('ab')

        time.sleep(1)
        for i in driver.find_elements_by_css_selector('#select2-id_developer-results li'):
            if i.text == "abc":
                i.click()
                break
        driver.find_element_by_css_selector("input.select2-search__field").send_keys(Keys.ESCAPE)

        driver.find_element_by_css_selector(".save").click()
        driver.find_element_by_link_text("Backlog").click()
        # create issues
        driver.find_element_by_link_text("New issue").click()
        driver.find_element_by_id("id_title").clear()
        driver.find_element_by_id("id_title").send_keys("Issue 1")
        driver.find_element_by_name("due_date").click()
        driver.find_element_by_name("due_date").send_keys(str(datetime.date.today().strftime("%m/%d/%Y")))
        driver.find_element_by_name("due_date").send_keys(Keys.TAB)  # close datepicker
        driver.find_element_by_css_selector("ul.select2-selection__rendered").click()
        driver.find_element_by_id("id_storypoints").clear()
        driver.find_element_by_id("id_storypoints").send_keys("1")
        driver.find_element_by_id("wmd-input-id_description").clear()
        driver.find_element_by_id("wmd-input-id_description").send_keys("aaa")
        driver.find_element_by_css_selector(".save").send_keys(Keys.RETURN)
        driver.find_element_by_link_text("Backlog").click()

        parentElement = driver.find_element_by_id("backlog_backlog")
        self.assertEqual(len(parentElement.find_elements_by_id("backlog_issue_1")), 1)

        driver.find_element_by_link_text("New sprint").click()
        driver.find_element_by_link_text("Backlog").click()

        parentElement = driver.find_element_by_id("backlog_backlog")
        self.assertEqual(len(parentElement.find_elements_by_id("backlog_issue_1")), 1)

        driver.find_element_by_id('ats1').submit()
        parentElement = driver.find_element_by_id("backlog_backlog")
        self.assertEqual(len(parentElement.find_elements_by_id("backlog_issue_1")), 0)
        parentElement = driver.find_element_by_id("backlog_sprint")
        self.assertEqual(len(parentElement.find_elements_by_id("sprint_issue_1")), 1)

        driver.find_element_by_link_text("Backlog").click()
        driver.find_element_by_link_text("New sprint").click()
        parentElement = driver.find_element_by_id("backlog_sprint")
        self.assertEqual(len(parentElement.find_elements_by_id("sprint_issue_1")), 0)

        # remove issue 1 from sprint
        driver.find_element_by_id("dropdownMenu1").click()
        driver.find_element_by_link_text("Sprint 1").click()
        driver.find_element_by_id('ats1').submit()
        parentElement = driver.find_element_by_id("backlog_sprint")
        self.assertEqual(len(parentElement.find_elements_by_id("sprint_issue_1")), 0)
        parentElement = driver.find_element_by_id("backlog_backlog")
        self.assertEqual(len(parentElement.find_elements_by_id("backlog_issue_1")), 1)

        driver.find_element_by_link_text("Backlog").click()

        # create new issue and add to sprint
        issue = Issue(title="Issue 2",
                      project=Project.objects.first(),
                      kanbancol=KanbanColumn.objects.first(),
                      type="Bug"
                      )
        issue.save()
        driver.find_element_by_link_text("Backlog").click()
        driver.find_element_by_id('ats2').submit()
        driver.find_element_by_id("startsprint").click()
        self.assertNotIn("Start", driver.page_source)
        driver.find_element_by_link_text("Sprintboard").click()
        self.assertEqual("Issue 2", driver.find_element_by_id("issue_title_2").text)
        self.assertNotIn("Issue 1", driver.page_source)
        driver.find_element_by_link_text("Backlog").click()
        driver.find_element_by_link_text("Stop").click()
        driver.find_element_by_id("finish_sprint").click()
        self.assertNotIn("Sprint 1", driver.page_source)
        driver.find_element_by_link_text("Backlog").click()
        parentElement = driver.find_element_by_id("backlog_backlog")
        self.assertEqual(len(parentElement.find_elements_by_id("backlog_issue_1")), 1)
        driver.find_element_by_link_text("New sprint").click()
        parentElement = driver.find_element_by_id("backlog_backlog")
        self.assertEqual(len(parentElement.find_elements_by_id("backlog_issue_2")), 1)

        # add issue to sprint2 and start it
        driver.find_element_by_id('ats1').submit()
        driver.find_element_by_id("startsprint").click()

        # go to sprintboard and move issue through kanban lines
        driver.find_element_by_link_text("Sprintboard").click()
        self.assertIn("notvisible", driver.page_source)
        self.assertEqual("Issue 1", driver.find_element_by_id("issue_title_1").text)
        driver.find_element_by_id('rcol1').submit()
        self.assertEqual("Issue 1", driver.find_element_by_id("issue_title_1").text)
        driver.find_element_by_id('rcol1').submit()
        self.assertEqual("Issue 1", driver.find_element_by_id("issue_title_1").text)
        self.assertIn("notvisible", driver.page_source)
        driver.find_element_by_id('lcol1').submit()
        self.assertEqual("Issue 1", driver.find_element_by_id("issue_title_1").text)
        driver.find_element_by_id('lcol1').submit()
        self.assertEqual("Issue 1", driver.find_element_by_id("issue_title_1").text)
        self.assertIn("notvisible", driver.page_source)

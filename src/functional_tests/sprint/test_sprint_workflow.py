"""
Iguana (c) by Marc Ammon, Moritz Fickenscher, Lukas Fridolin, Michael Gunselmann, Katrin Raab, Christian Strate

Iguana is licensed under BSD-2-Clause License.

Redistribution and use in source and binary forms, with or without modification,
are permitted provided that the following conditions are met:

   1. Redistributions of source code must retain the above copyright notice,
      this list of conditions and the following disclaimer.
   2. Redistributions in binary form must reproduce the above copyright notice,
      this list of conditions and the following disclaimer
      in the documentation and/or other materials provided with the distribution.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES,
INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS
BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
(INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS;
OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE,
EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
"""
from django.test import Client
from lib.selenium_test_case import SeleniumTestCase
from selenium.webdriver.common.by import By
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
        driver.find_element(By.LINK_TEXT, "Create new project").click()
        driver.find_element(By.ID, "id_name").clear()
        driver.find_element(By.ID, "id_name").send_keys("Fancy Project")
        driver.find_element(By.ID, "id_name_short").clear()
        driver.find_element(By.ID, "id_name_short").send_keys("FYP")
        driver.find_element(By.ID, "id_description").clear()
        driver.find_element(By.ID, "id_description").send_keys("Fancy description")
        driver.find_element(By.CSS_SELECTOR, "ul.select2-selection__rendered").click()
        driver.find_element(By.CSS_SELECTOR, "input.select2-search__field").send_keys('ab')

        time.sleep(1)
        for i in driver.find_elements(By.CSS_SELECTOR, '#select2-id_developer-results li'):
            if i.text == "abc":
                i.click()
                break
        driver.find_element(By.CSS_SELECTOR, "input.select2-search__field").send_keys(Keys.ESCAPE)

        driver.find_element(By.CSS_SELECTOR, ".save").click()
        driver.find_element(By.LINK_TEXT, "Backlog").click()
        # create issues
        driver.find_element(By.LINK_TEXT, "New issue").click()
        driver.find_element(By.ID, "id_title").clear()
        driver.find_element(By.ID, "id_title").send_keys("Issue 1")
        driver.find_element(By.NAME, "due_date").click()
        driver.find_element(By.NAME, "due_date").send_keys(str(datetime.date.today().strftime("%m/%d/%Y")))
        driver.find_element(By.NAME, "due_date").send_keys(Keys.TAB)  # close datepicker
        driver.find_element(By.CSS_SELECTOR, "ul.select2-selection__rendered").click()
        driver.find_element(By.ID, "id_storypoints").clear()
        driver.find_element(By.ID, "id_storypoints").send_keys("1")
        driver.find_element(By.ID, "wmd-input-id_description").clear()
        driver.find_element(By.ID, "wmd-input-id_description").send_keys("aaa")
        driver.find_element(By.CSS_SELECTOR, ".save").send_keys(Keys.RETURN)
        driver.find_element(By.LINK_TEXT, "Backlog").click()

        parentElement = driver.find_element(By.ID, "backlog_backlog")
        self.assertEqual(len(parentElement.find_elements(By.ID, "backlog_issue_1")), 1)

        driver.find_element(By.LINK_TEXT, "New sprint").click()
        driver.find_element(By.LINK_TEXT, "Backlog").click()

        parentElement = driver.find_element(By.ID, "backlog_backlog")
        self.assertEqual(len(parentElement.find_elements(By.ID, "backlog_issue_1")), 1)

        driver.find_element(By.ID, 'ats1').submit()
        parentElement = driver.find_element(By.ID, "backlog_backlog")
        self.assertEqual(len(parentElement.find_elements(By.ID, "backlog_issue_1")), 0)
        parentElement = driver.find_element(By.ID, "backlog_sprint")
        self.assertEqual(len(parentElement.find_elements(By.ID, "sprint_issue_1")), 1)

        driver.find_element(By.LINK_TEXT, "Backlog").click()
        driver.find_element(By.LINK_TEXT, "New sprint").click()
        parentElement = driver.find_element(By.ID, "backlog_sprint")
        self.assertEqual(len(parentElement.find_elements(By.ID, "sprint_issue_1")), 0)

        # remove issue 1 from sprint
        driver.find_element(By.ID, "dropdownMenu1").click()
        driver.find_element(By.LINK_TEXT, "Sprint 1").click()
        driver.find_element(By.ID, 'ats1').submit()
        parentElement = driver.find_element(By.ID, "backlog_sprint")
        self.assertEqual(len(parentElement.find_elements(By.ID, "sprint_issue_1")), 0)
        parentElement = driver.find_element(By.ID, "backlog_backlog")
        self.assertEqual(len(parentElement.find_elements(By.ID, "backlog_issue_1")), 1)

        driver.find_element(By.LINK_TEXT, "Backlog").click()

        # create new issue and add to sprint
        issue = Issue(title="Issue 2",
                      project=Project.objects.first(),
                      kanbancol=KanbanColumn.objects.first(),
                      type="Bug"
                      )
        issue.save()
        driver.find_element(By.LINK_TEXT, "Backlog").click()
        driver.find_element(By.ID, 'ats2').submit()
        driver.find_element(By.ID, "startsprint").click()
        self.assertNotIn("Start", driver.page_source)
        driver.find_element(By.LINK_TEXT, "Sprintboard").click()
        self.assertEqual("Issue 2", driver.find_element(By.ID, "issue_title_2").text)
        self.assertNotIn("Issue 1", driver.page_source)
        driver.find_element(By.LINK_TEXT, "Backlog").click()
        driver.find_element(By.LINK_TEXT, "Stop").click()
        driver.find_element(By.ID, "finish_sprint").click()
        self.assertNotIn("Sprint 1", driver.page_source)
        driver.find_element(By.LINK_TEXT, "Backlog").click()
        parentElement = driver.find_element(By.ID, "backlog_backlog")
        self.assertEqual(len(parentElement.find_elements(By.ID, "backlog_issue_1")), 1)
        driver.find_element(By.LINK_TEXT, "New sprint").click()
        parentElement = driver.find_element(By.ID, "backlog_backlog")
        self.assertEqual(len(parentElement.find_elements(By.ID, "backlog_issue_2")), 1)

        # add issue to sprint2 and start it
        driver.find_element(By.ID, 'ats1').submit()
        driver.find_element(By.ID, "startsprint").click()

        # go to sprintboard and move issue through kanban lines
        driver.find_element(By.LINK_TEXT, "Sprintboard").click()
        self.assertIn("notvisible", driver.page_source)
        self.assertEqual("Issue 1", driver.find_element(By.ID, "issue_title_1").text)
        driver.find_element(By.ID, 'rcol1').submit()
        self.assertEqual("Issue 1", driver.find_element(By.ID, "issue_title_1").text)
        driver.find_element(By.ID, 'rcol1').submit()
        self.assertEqual("Issue 1", driver.find_element(By.ID, "issue_title_1").text)
        self.assertIn("notvisible", driver.page_source)
        driver.find_element(By.ID, 'lcol1').submit()
        self.assertEqual("Issue 1", driver.find_element(By.ID, "issue_title_1").text)
        driver.find_element(By.ID, 'lcol1').submit()
        self.assertEqual("Issue 1", driver.find_element(By.ID, "issue_title_1").text)
        self.assertIn("notvisible", driver.page_source)

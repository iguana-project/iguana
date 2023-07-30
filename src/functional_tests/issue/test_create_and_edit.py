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
from selenium.webdriver.support.ui import Select
import datetime
import time

from django.contrib.auth import get_user_model
from project.models import Project
from kanbancol.models import KanbanColumn
from issue.models import Issue


# TODO we might wanna test the href-links on those pages
class CreateAndEditTest(SeleniumTestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user('a', 'b', 'c')
        self.project = Project(creator=self.user, name="asdf", name_short="PRJ")
        self.project.save()
        self.project.manager.add(self.user)
        self.project.developer.add(self.user)
        self.project2 = Project(creator=self.user, name="2ndproj", name_short="PRJ2")
        self.project2.save()
        self.project2.developer.add(self.user)
        self.kanban = KanbanColumn(name='KanCol', project=self.project2, position=4)
        self.kanban.save()

        # Uses the cookie hack from:
        # https://stackoverflow.com/questions/22494583/login-with-code-when-using-liveservertestcase-with-django
        client = Client()
        client.login(username='a', password='c')
        self.cookie = client.cookies['sessionid']
        self.selenium.get("{}{}".format(self.live_server_url, reverse('invite_users:invite_users')))
        self.selenium.add_cookie({'name': 'sessionid', 'value': self.cookie.value, 'secure': False, 'path': '/'})
        self.selenium.refresh()

    def test_reachable_and_elements_exist(self):
        # TODO TESTCASE
        # TODO for each site check it is available + check (some) content like the title + check existence of forms
        #      and their form elements by their ids!
        # TODO create => form
        # TODO edit => form
        pass

    def test_title_required(self):
        # TODO TESTCASE
        # TODO create => title
        # TODO edit => title
        pass

    def test_create(self):
        driver = self.selenium
        driver.get("{}{}".format(self.live_server_url, reverse('issue:create',
                                                               kwargs={'project': self.project.name_short})))

        title = "title"
        driver.find_element(By.ID, "id_title").send_keys(title)

        # assert that initially selected kanbancol is 'Todo'
        self.assertEqual(Select(driver.find_element(By.ID, "id_kanbancol")).first_selected_option.text, "Todo")

        # assert that project has 4 (3 default + --- line) kanban colums
        self.assertEqual(len(Select(driver.find_element(By.ID, "id_kanbancol")).options), 4)

        Select(driver.find_element(By.ID, "id_kanbancol")).select_by_visible_text("Todo")
        driver.find_element(By.NAME, "due_date").click()
        driver.find_element(By.NAME, "due_date").send_keys(str(datetime.date.today().strftime("%m/%d/%Y")))
        driver.find_element(By.NAME, "due_date").send_keys(Keys.TAB)  # close datepicker
        # assert that we have one assignee in selection field
        driver.find_element(By.CSS_SELECTOR, "input.select2-search__field").click()
        self.assertEqual(len(driver.find_elements(By.CSS_SELECTOR, '#select2-id_assignee-results li')), 1)
        driver.find_element(By.CSS_SELECTOR, "input.select2-search__field").send_keys(Keys.ESCAPE)
        Select(driver.find_element(By.ID, "id_priority")).select_by_visible_text("High")
        driver.find_element(By.ID, "id_storypoints").clear()
        driver.find_element(By.ID, "id_storypoints").send_keys("2")

        # assert that project has no related issues to choose from (only one issue present in proj2)
        # one item present: No items found
        driver.find_element(By.XPATH, "(//input[@type='search'])[2]").send_keys(Keys.RETURN)
        time.sleep(1)
        self.assertEqual(len(driver.find_elements(By.CSS_SELECTOR, '#select2-id_dependsOn-results li')), 1)
        for i in driver.find_elements(By.CSS_SELECTOR, '#select2-id_dependsOn-results li'):
            self.assertEqual(i.text, "No results found")

        driver.find_element(By.ID, "wmd-input-id_description").clear()
        driver.find_element(By.ID, "wmd-input-id_description").send_keys("blubber")
        driver.find_element(By.ID, "id_submit_create").click()
        self.assertIn(title, driver.page_source)

    def test_number_kanbancolumns_for_case_not_default(self):
        driver = self.selenium
        issue = Issue(title="title", kanbancol=KanbanColumn.objects.get(project=self.project, name="Todo"),
                      due_date=str(datetime.date.today()), priority=3, storypoints=2, description="blubber",
                      project=self.project
                      )
        issue.save()
        issue.assignee.add(self.user)

        driver.get("{}{}".format(self.live_server_url, reverse('issue:create',
                                                               kwargs={'project': self.project2.name_short})))
        driver.find_element(By.ID, "id_title").send_keys("title")
        # assert that 2nd project has one kanban col more
        self.assertEqual(len(Select(driver.find_element(By.ID, "id_kanbancol")).options), 5)

        # assert that dependsOn now has one entry
        driver.get('{}{}'.format(self.live_server_url, reverse('backlog:backlog',
                                                               kwargs={'project': self.project.name_short}
                                                               )))
        driver.find_element(By.LINK_TEXT, "New issue").click()
        driver.find_element(By.XPATH, "(//input[@type='search'])[2]").send_keys('\n')
        time.sleep(1)
        self.assertEqual(len(driver.find_elements(By.CSS_SELECTOR, '#select2-id_dependsOn-results li')), 1)
        for i in driver.find_elements(By.CSS_SELECTOR, '#select2-id_dependsOn-results li'):
            self.assertIn("title", i.text)

    def test_edit_same_settings_as_set(self):
        driver = self.selenium
        issue = Issue(title="title", kanbancol=KanbanColumn.objects.get(project=self.project, name="Todo"),
                      due_date=str(datetime.date.today()), priority=3, storypoints=2, description="blubber",
                      project=self.project
                      )
        issue.save()
        issue.assignee.add(self.user)
        driver.get("{}{}".format(self.live_server_url, reverse('issue:edit',
                                 kwargs={'project': self.project.name_short, 'sqn_i': issue.number})))
        self.assertEqual(len(Select(driver.find_element(By.ID, "id_kanbancol")).options), 4)

        # issue must not depend on itself
        driver.find_element(By.XPATH, "(//input[@type='search'])[2]").send_keys('\n')
        time.sleep(1)
        self.assertEqual(len(driver.find_elements(By.CSS_SELECTOR, '#select2-id_dependsOn-results li')), 1)
        for i in driver.find_elements(By.CSS_SELECTOR, '#select2-id_dependsOn-results li'):
            self.assertEqual(i.text, "No results found")

    def test_dependencies(self):
        driver = self.selenium

        # create two issues
        issue = Issue(title="title", kanbancol=KanbanColumn.objects.get(project=self.project, name="Todo"),
                      due_date=str(datetime.date.today()), priority=3, storypoints=2, description="blubber",
                      project=self.project
                      )
        issue.save()
        issue.assignee.add(self.user)
        issue = Issue(title="title", kanbancol=KanbanColumn.objects.get(project=self.project, name="Todo"),
                      due_date=str(datetime.date.today()), priority=3, storypoints=2, description="blubber",
                      project=self.project
                      )
        issue.save()
        issue.assignee.add(self.user)

        driver.get('{}{}'.format(self.live_server_url, reverse('backlog:backlog',
                                                               kwargs={'project': self.project.name_short}
                                                               )))

        driver.find_element(By.LINK_TEXT, "PRJ-1").click()
        driver.find_element(By.ID, "issue_detail_edit_link").click()
        driver.find_element(By.XPATH, "(//input[@type='search'])[2]").send_keys('\n')
        time.sleep(1)
        self.assertEqual(len(driver.find_elements(By.CSS_SELECTOR, '#select2-id_dependsOn-results li')), 1)
        for i in driver.find_elements(By.CSS_SELECTOR, '#select2-id_dependsOn-results li'):
            i.click()
        driver.find_element(By.ID, "id_submit_edit").click()
        self.assertIn('Depends on', driver.page_source)
        self.assertIn('PRJ-2', driver.page_source)
        url = driver.current_url
        driver.find_element(By.LINK_TEXT, "title").click()
        self.assertIn('Dependent issues', driver.page_source)
        self.assertIn('PRJ-1', driver.page_source)
        driver.find_element(By.LINK_TEXT, "title").click()
        self.assertEqual(url, driver.current_url)

    def test_edit_change_settings(self):
        # TODO TESTCASE
        pass

    def test_delete_issue(self):
        # TODO TESTCASE
        pass

    def test_keep_and_dont_delete_issue(self):
        # TODO TESTCASE
        pass

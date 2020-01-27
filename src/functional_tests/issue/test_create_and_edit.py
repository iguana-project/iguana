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
        driver.find_element_by_id("id_title").send_keys(title)

        # assert that initially selected kanbancol is 'Todo'
        self.assertEqual(Select(driver.find_element_by_id("id_kanbancol")).first_selected_option.text, "Todo")

        # assert that project has 4 (3 default + --- line) kanban colums
        self.assertEqual(len(Select(driver.find_element_by_id("id_kanbancol")).options), 4)

        Select(driver.find_element_by_id("id_kanbancol")).select_by_visible_text("Todo")
        driver.find_element_by_name("due_date").click()
        driver.find_element_by_name("due_date").send_keys(str(datetime.date.today().strftime("%m/%d/%Y")))
        driver.find_element_by_name("due_date").send_keys(Keys.TAB)  # close datepicker
        # assert that we have one assignee in selection field
        driver.find_element_by_css_selector("input.select2-search__field").click()
        self.assertEqual(len(driver.find_elements_by_css_selector('#select2-id_assignee-results li')), 1)
        driver.find_element_by_css_selector("input.select2-search__field").send_keys(Keys.ESCAPE)
        Select(driver.find_element_by_id("id_priority")).select_by_visible_text("High")
        driver.find_element_by_id("id_storypoints").clear()
        driver.find_element_by_id("id_storypoints").send_keys("2")

        # assert that project has no related issues to choose from (only one issue present in proj2)
        # one item present: No items found
        driver.find_element_by_xpath("(//input[@type='search'])[2]").send_keys(Keys.RETURN)
        time.sleep(1)
        self.assertEqual(len(driver.find_elements_by_css_selector('#select2-id_dependsOn-results li')), 1)
        for i in driver.find_elements_by_css_selector('#select2-id_dependsOn-results li'):
            self.assertEqual(i.text, "No results found")

        driver.find_element_by_id("wmd-input-id_description").clear()
        driver.find_element_by_id("wmd-input-id_description").send_keys("blubber")
        driver.find_element_by_id("id_submit_create").click()
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
        driver.find_element_by_id("id_title").send_keys("title")
        # assert that 2nd project has one kanban col more
        self.assertEqual(len(Select(driver.find_element_by_id("id_kanbancol")).options), 5)

        # assert that dependsOn now has one entry
        driver.get('{}{}'.format(self.live_server_url, reverse('backlog:backlog',
                                                               kwargs={'project': self.project.name_short}
                                                               )))
        driver.find_element_by_link_text("New issue").click()
        driver.find_element_by_xpath("(//input[@type='search'])[2]").send_keys('\n')
        time.sleep(1)
        self.assertEqual(len(driver.find_elements_by_css_selector('#select2-id_dependsOn-results li')), 1)
        for i in driver.find_elements_by_css_selector('#select2-id_dependsOn-results li'):
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
        self.assertEqual(len(Select(driver.find_element_by_id("id_kanbancol")).options), 4)

        # issue must not depend on itself
        driver.find_element_by_xpath("(//input[@type='search'])[2]").send_keys('\n')
        time.sleep(1)
        self.assertEqual(len(driver.find_elements_by_css_selector('#select2-id_dependsOn-results li')), 1)
        for i in driver.find_elements_by_css_selector('#select2-id_dependsOn-results li'):
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

        driver.find_element_by_link_text("PRJ-1").click()
        driver.find_element_by_id("issue_detail_edit_link").click()
        driver.find_element_by_xpath("(//input[@type='search'])[2]").send_keys('\n')
        time.sleep(1)
        self.assertEqual(len(driver.find_elements_by_css_selector('#select2-id_dependsOn-results li')), 1)
        for i in driver.find_elements_by_css_selector('#select2-id_dependsOn-results li'):
            i.click()
        driver.find_element_by_id("id_submit_edit").click()
        self.assertIn('Depends on', driver.page_source)
        self.assertIn('PRJ-2', driver.page_source)
        url = driver.current_url
        driver.find_element_by_link_text("title").click()
        self.assertIn('Dependent issues', driver.page_source)
        self.assertIn('PRJ-1', driver.page_source)
        driver.find_element_by_link_text("title").click()
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

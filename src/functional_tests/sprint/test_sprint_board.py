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
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import WebDriverException
from django.urls import reverse
import datetime
import time

from django.contrib.auth import get_user_model
from issue.models import Issue
from kanbancol.models import KanbanColumn
from project.models import Project


# NOTE: This tests a lot of funtionality - even across app boarders
#       So it contains redundant testing of other apps, but one bigger test is nice to have
class SprintBoardTest(StaticSeleniumTestCase):

    def setUp(self):
        self.user = get_user_model().objects.create_user('a', 'b', 'c')
        # Uses the cookie hack from:
        # https://stackoverflow.com/questions/22494583/login-with-code-when-using-liveservertestcase-with-django
        client = Client()
        client.login(username='a', password='c')
        self.cookie = client.cookies['sessionid']
        self.selenium.get("{}{}".format(self.live_server_url, reverse('invite_users:invite_users')))
        self.selenium.add_cookie({'name': 'sessionid', 'value': self.cookie.value, 'secure': False, 'path': '/'})
        self.selenium.refresh()

    def test_board_drag_n_drop(self):
        def ajax_complete(driver):
            try:
                return 0 == driver.execute_script("return jQuery.active")
            except WebDriverException:
                pass

        # create project and issues
        driver = self.selenium
        project = Project(name='TestProjekt', name_short='TP', creator=self.user)
        project.save()
        project.developer.add(self.user)
        issue1 = Issue(project=project, title="TestIssue1")
        issue2 = Issue(project=project, title="TestIssue2")
        issue1.save()
        issue2.save()

        driver.get("{}{}".format(self.live_server_url, reverse('issue:projList',
                                                               kwargs={'project': project.name_short}
                                                               )))
        self.assertEqual(issue1.kanbancol.position, 0)
        self.assertEqual(issue2.kanbancol.position, 0)
        driver.find_element_by_link_text("Board").click()

        # move issue1 and issue2
        source_element = driver.find_element_by_id('board_issue_1')
        dest_element = driver.find_element_by_id('sortable1')
        ActionChains(driver).drag_and_drop(source_element, dest_element).perform()

        source_element = driver.find_element_by_id('board_issue_2')
        dest_element = driver.find_element_by_id('sortable2')
        ActionChains(driver).drag_and_drop(source_element, dest_element).perform()

        WebDriverWait(driver, 10).until(ajax_complete,
                                        "Timeout waiting for page to load"
                                        )
        # assert kanbancol has changed
        issue1.refresh_from_db()
        issue2.refresh_from_db()
        # self.assertEqual(issue1.kanbancol.position, 1)
        # self.assertEqual(issue2.kanbancol.position, 2)

    def test_board_order_by(self):

        # driver.find_element_by_id("dropdownMenu1").click()
        # driver.find_element_by_link_text("Sprint 1").click()

        # create project and issues
        driver = self.selenium
        project = Project(name='TestProjekt', name_short='TP', creator=self.user)
        project.save()
        project.developer.add(self.user)
        issue1 = Issue(project=project, title="TestIssue1", priority=4, type='Story')
        issue2 = Issue(project=project, title="TestIssue2", priority=0, type='Bug')
        issue3 = Issue(project=project, title="TestIssue3", priority=3, type='Task')
        issue4 = Issue(project=project, title="TestIssue3", priority=2, type='Task')
        issue5 = Issue(project=project, title="TestIssue3", priority=0, type='Story')

        issue1.save()
        issue2.save()
        issue3.save()
        issue4.save()
        issue5.save()

        # check order_by number
        driver.get("{}{}".format(self.live_server_url, reverse('issue:projList',
                                                               kwargs={'project': project.name_short}
                                                               )))
        col = driver.find_element_by_id("sortable0")
        issues = col.find_elements_by_class_name("issuecard")
        for i in range(len(issues)-1):
            self.assertEqual(issues[i].get_attribute("id") < issues[i+1].get_attribute("id"), True)

        # check order_by priority
        driver.get("{}{}".format(self.live_server_url, reverse('issue:projList',
                                                               kwargs={'project': project.name_short}
                                                               ))+"?order_by=priority")
        col = driver.find_element_by_id("sortable0")
        issues = col.find_elements_by_class_name("issuecard")
        for i in range(len(issues)-1):
            self.assertEqual(issues[i].get_attribute("data-priority") >= issues[i+1].get_attribute("data-priority"),
                             True)

        # check order_by title
        driver.get("{}{}".format(self.live_server_url, reverse('issue:projList',
                                                               kwargs={'project': project.name_short}
                                                               ))+"?order_by=title")
        col = driver.find_element_by_id("sortable0")
        issues = col.find_elements_by_class_name("issuecard")
        for i in range(len(issues)-1):
            self.assertEqual(issues[i].get_attribute("data-title") <= issues[i+1].get_attribute("data-title"), True)

        # check order_by Type
        driver.get("{}{}".format(self.live_server_url, reverse('issue:projList',
                                                               kwargs={'project': project.name_short}
                                                               ))+"?order_by=type")
        col = driver.find_element_by_id("sortable0")
        issues = col.find_elements_by_class_name("issuecard")
        for i in range(len(issues)-1):
            self.assertEqual(issues[i].get_attribute("data-type") <= issues[i+1].get_attribute("data-type"), True)

    def test_board_drag_n_drop_order_by(self):
        def ajax_complete(driver):
            try:
                return 0 == driver.execute_script("return jQuery.active")
            except WebDriverException:
                pass

        driver = self.selenium
        project = Project(name='TestProjekt', name_short='TP', creator=self.user)
        project.save()
        project.developer.add(self.user)
        issue1 = Issue(project=project, title="TestIssue1", priority=4, type='Story')
        issue2 = Issue(project=project, title="TestIssue2", priority=0, type='Bug')
        issue3 = Issue(project=project, title="TestIssue3", priority=3, type='Task')
        issue4 = Issue(project=project, title="TestIssue3", priority=2, type='Task')
        issue5 = Issue(project=project, title="TestIssue3", priority=0, type='Story')

        issue1.save()
        issue2.save()
        issue3.save()
        issue4.save()
        issue5.save()

        # switch to ordered_by priority
        driver.get("{}{}".format(self.live_server_url, reverse('issue:projList',
                                                               kwargs={'project': project.name_short}
                                                               ))+"?order_by=priority")

        # all issues in col_0 ordered by priority
        col = driver.find_element_by_id("sortable0")
        issues = col.find_elements_by_class_name("issuecard")
        for i in range(len(issues)-1):
            self.assertEqual(issues[i].get_attribute("data-priority") >= issues[i+1].get_attribute("data-priority"),
                             True)

        # move issue2 to col_1
        source_element = driver.find_element_by_id('board_issue_2')
        dest_element = driver.find_element_by_id('sortable1')
        ActionChains(driver).drag_and_drop(source_element, dest_element).perform()

        # move issue1 to col_1
        source_element = driver.find_element_by_id('board_issue_1')
        dest_element = driver.find_element_by_id('sortable1')
        ActionChains(driver).drag_and_drop(source_element, dest_element).perform()

        # drag and drop implementation of selenium doesn't perform drag and drop like a user would do
        # the jquery ui sortable event 'stop' doesn't get triggered, the issues will not be sorted by 'order_by' after
        # drag n drop. we need to refresh
        driver.refresh()

        # all issues in col_0 ordered by priority
        col = driver.find_element_by_id("sortable0")
        issues = col.find_elements_by_class_name("issuecard")
        for i in range(len(issues)-1):
            self.assertEqual(issues[i].get_attribute("data-priority") >= issues[i+1].get_attribute("data-priority"),
                             True)

        # all issues in col_1 ordered by priority
        col = driver.find_element_by_id("sortable1")
        issues = col.find_elements_by_class_name("issuecard")
        for i in range(len(issues)-1):
            self.assertEqual(issues[i].get_attribute("data-priority") >= issues[i+1].get_attribute("data-priority"),
                             True)

    def test_board_filter_my_issues(self):
        driver = self.selenium
        project = Project(name='TestProjekt', name_short='TP', creator=self.user)
        project.save()
        project.developer.add(self.user)
        issue1 = Issue(project=project, title="TestIssue1", priority=4, type='Story')
        issue2 = Issue(project=project, title="TestIssue2", priority=0, type='Bug')
        issue3 = Issue(project=project, title="TestIssue3", priority=3, type='Task')
        issue4 = Issue(project=project, title="TestIssue3", priority=2, type='Task')
        issue5 = Issue(project=project, title="TestIssue3", priority=0, type='Story')

        issue1.save()
        issue2.save()
        issue3.save()
        issue4.save()
        issue5.save()

        driver.get("{}{}".format(self.live_server_url, reverse('issue:projList',
                                                               kwargs={'project': project.name_short}
                                                               )))

        # 5 issues in col 0
        col = driver.find_element_by_id("sortable0")
        issues = col.find_elements_by_class_name("issuecard")
        self.assertEqual(len(issues), 5)

        issue1.assignee.add(self.user)

        driver.get("{}{}".format(self.live_server_url, reverse('issue:projList',
                                                               kwargs={'project': project.name_short}
                                                               ))+"?myissues=true")

        # 1 issue in col 0
        col = driver.find_element_by_id("sortable0")
        issues = col.find_elements_by_class_name("issuecard")
        self.assertEqual(len(issues), 1)

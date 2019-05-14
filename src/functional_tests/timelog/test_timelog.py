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
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.keys import Keys
from datetime import timedelta

from django.contrib.auth import get_user_model
from project.models import Project
from kanbancol.models import KanbanColumn
from issue.models import Issue
from timelog.models import Timelog


# TODO TESTCASE refactoring + write testcases
class TimelogTest(SeleniumTestCase):

    def setUp(self):
        self.user = get_user_model().objects.create_user('test', 'test@test.com', 'test')
        self.project = Project(creator=self.user, name_short='PRJ')
        self.project.save()
        self.project.developer.add(self.user)
        # NOTE: those elements get modified by some of those tests, so this shall NOT be created in setUpTestData()
        self.issue = Issue(title='issue title',
                           project=self.project,
                           due_date='2016-12-16',
                           storypoints='3'
                           )
        self.issue.save()
        self.issue2 = Issue(title='title2',
                            project=self.project,
                            due_date='2016-12-16',
                            storypoints='3'
                            )
        self.issue2.save()
        self.issue.assignee.add(self.user)

        # Uses the cookie hack from:
        # https://stackoverflow.com/questions/22494583/login-with-code-when-using-liveservertestcase-with-django
        client = Client()
        client.login(username='test', password='test')
        self.cookie = client.cookies['sessionid']
        self.selenium.get("{}{}".format(self.live_server_url, reverse('timelog:loginfo')))
        self.selenium.add_cookie({'name': 'sessionid', 'value': self.cookie.value, 'secure': False, 'path': '/'})
        self.selenium.refresh()

    def test_workflow(self):
        driver = self.selenium
        driver.get(self.live_server_url + reverse('landing_page:home'))
        driver.find_element_by_link_text("Projects").click()
        driver.find_element_by_link_text("Create new project").click()
        driver.find_element_by_id("id_name").clear()
        driver.find_element_by_id("id_name").send_keys("Test-Project")
        driver.find_element_by_id("id_name_short").clear()
        driver.find_element_by_id("id_name_short").send_keys("TTT")
        driver.find_element_by_id("id_description").clear()
        driver.find_element_by_id("id_description").send_keys("Description")
        driver.find_element_by_id("id_submit_create").click()
        driver.find_element_by_link_text("Board").click()
        driver.find_element_by_id("expression").clear()
        driver.find_element_by_id("expression").send_keys("Issue" + Keys.RETURN)
        driver.find_element_by_id("expression").clear()
        driver.find_element_by_id("expression").send_keys("Another" + Keys.RETURN)
        driver.find_element_by_id("expression").clear()
        driver.find_element_by_id("expression").send_keys("So funny" + Keys.RETURN)
        driver.find_element_by_id("expression").clear()
        driver.find_element_by_id("expression").send_keys(">2 +10m" + Keys.RETURN)
        driver.find_element_by_id("expression").clear()
        driver.find_element_by_id("expression").send_keys(">3 +1h" + Keys.RETURN)
        driver.find_element_by_id("expression").clear()
        driver.find_element_by_id("expression").send_keys(">1 +15m" + Keys.RETURN)
        driver.find_element_by_link_text("TTT-1").click()
        self.assertIn("15 Minutes", driver.find_element_by_id("issue_detail_log_1").text)
        driver.find_element_by_link_text("TTT").click()
        driver.find_element_by_link_text("TTT-2").click()
        self.assertIn("10 Minutes", driver.find_element_by_id("issue_detail_log_1").text)
        driver.find_element_by_link_text("TTT").click()
        driver.find_element_by_link_text("TTT-3").click()
        self.assertIn("1 Hour", driver.find_element_by_id("issue_detail_log_1").text)
        driver.find_element_by_css_selector("#issue_detail_log_1 > div > a > span.glyphicon.glyphicon-pencil").click()
        driver.find_element_by_id("id_time").clear()
        driver.find_element_by_id("id_time").send_keys("50m")
        driver.find_element_by_id("id_submit_save_timelog_change").click()
        self.assertIn("50 Minutes", driver.find_element_by_id("issue_detail_log_1").text)
        driver.find_element_by_link_text("Timelogging").click()
        self.assertEqual("total: 1 Hour and 15 Minutes",
                         driver.find_element_by_css_selector("li.list-group-item > b").text)
        driver.find_element_by_id("timelog").click()
        self.assertIn("10 Minutes", driver.find_element_by_css_selector("#log_1 > div.row > div.col-xs-5").text)
        self.assertIn("15 Minutes", driver.find_element_by_css_selector("#log_2 > div.row > div.col-xs-5").text)
        self.assertIn("50 Minutes", driver.find_element_by_css_selector("#log_3 > div.row > div.col-xs-5").text)
        driver.find_element_by_link_text("Activity").click()
        driver.find_element_by_link_text("Last Week").click()
        driver.find_element_by_id("dropdownMenu1").click()
        driver.find_element_by_id("content").click()
        driver.find_element_by_id("dropdownMenu1").click()
        driver.find_element_by_link_text("Activity").click()
        driver.find_element_by_id("dropdownMenu1").click()
        driver.find_element_by_xpath("//div[@id='content']/div/div[2]/div/div/ul/li[2]/a/b").click()
        driver.find_element_by_id("cal-heatmap-previous").click()
        driver.find_element_by_id("cal-heatmap-next").click()
        driver.find_element_by_css_selector("i.caret").click()
        driver.find_element_by_link_text("Profile").click()
        self.assertIn("test", driver.find_element_by_css_selector("h1.page-header").text)
        driver.find_element_by_id("show_actions").click()

    def test_reachable_and_elements_exist(self):
        # TODO TESTCASE
        # TODO for each site check it is available + check (some) content like the title + check existence of forms
        #      and their form elements by their ids!
        # TODO timelog:loginfo
        # TODO project/<proj_pattern>/issue/<issue_sqn>/log
        pass

    def test_time_field_required(self):
        # TODO TESTCASE
        # TODO timelog:loginfo
        # TODO project/<proj_pattern>/issue/<issue_sqn>/log
        pass

    def test_issue_loglist(self):
        # TODO project/<proj_pattern>/issue/<issue_sqn>/logs
        # TODO this should only test if the elements created with models are listed here
        pass

    # TODO this should only test if the elements created with models are listed here (s.b.)
    def test_overview_log_form(self):
        driver = self.selenium
        driver.get(self.live_server_url + reverse('timelog:loginfo'))
        driver.find_element_by_id("id_time").send_keys("2h")
        self.assertEqual(len(Select(driver.find_element_by_id("id_issue")).options), 2)
        Select(driver.find_element_by_id("id_issue")).select_by_visible_text("issue title")
        driver.find_element_by_css_selector(".save").click()
        entry = driver.find_element_by_id("log_1")
        self.assertIn('issue title', entry.text)
        self.assertIn('2 Hours', entry.text)
        driver.find_element_by_id("log_edit_link_1").click()
        driver.find_element_by_id("id_time").clear()
        driver.find_element_by_id("id_time").send_keys("1h")
        driver.find_element_by_css_selector(".save").click()
        driver.get(self.live_server_url + reverse('timelog:loginfo'))
        entry = driver.find_element_by_id("log_1")
        self.assertIn('issue title', entry.text)
        self.assertIn('1 Hour', entry.text)
        self.issue2.assignee.add(self.user)
        self.selenium.refresh()
        self.assertEqual(len(Select(driver.find_element_by_id("id_issue")).options), 3)
        driver.find_element_by_id("id_time").send_keys("5h")
        Select(driver.find_element_by_id("id_issue")).select_by_visible_text("title2")
        driver.find_element_by_css_selector(".save").click()
        driver.get('{}{}'.format(self.live_server_url, reverse('issue:detail',
                                                               kwargs={'project': self.project.name_short,
                                                                       'sqn_i': self.issue2.number
                                                                       }
                                                               )))
        entry = driver.find_element_by_id("issue_detail_log_1")
        self.assertIn('5 Hours', entry.text)

        driver.get(self.live_server_url + reverse('timelog:loginfo'))
        driver.find_element_by_id("log_delete_link_2").click()
        driver.find_element_by_id('id_submit_delete').click()

        driver.get('{}{}'.format(self.live_server_url, reverse('issue:detail',
                                                               kwargs={'project': self.project.name_short,
                                                                       'sqn_i': self.issue2.number
                                                                       }
                                                               )
                                 )
                   )
        self.assertNotIn('5 Hours', driver.page_source)

    def test_issue_detail_log_form(self):
        driver = self.selenium
        t = Timelog(user=self.user, issue=self.issue, time=timedelta(hours=3))
        t.save()
        driver.get('{}{}'.format(self.live_server_url, reverse('issue:detail',
                                                               kwargs={'project': self.project.name_short,
                                                                       'sqn_i': self.issue.number
                                                                       }
                                                               )))
        entry = driver.find_element_by_id("issue_detail_log_1")
        self.assertIn('3 Hour', entry.text)

    def test_delete_timelog(self):
        # TODO TESTCASE
        pass

    def test_keep_and_dont_delete_timelog(self):
        # TODO
        # TODO TESTCASE
        pass

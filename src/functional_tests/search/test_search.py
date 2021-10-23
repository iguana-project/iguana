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
import time

from django.contrib.auth import get_user_model
from project.models import Project
from issue.models import Issue
from search.models import Search
from search.frontend import SearchFrontend


class SearchTest(SeleniumTestCase):

    def setUp(self):

        self.user = get_user_model().objects.create_user('a', 'b', 'c')
        self.user.last_name = 'Issue'
        self.user.save()
        # Uses the cookie hack from:
        # https://stackoverflow.com/questions/22494583/login-with-code-when-using-liveservertestcase-with-django
        client = Client()
        client.login(username='a', password='c')
        self.cookie = client.cookies['sessionid']
        self.selenium.get('{}{}'.format(self.live_server_url, reverse('landing_page:home')))
        self.selenium.add_cookie({'name': 'sessionid', 'value': self.cookie.value, 'secure': False, 'path': '/'})
        self.selenium.refresh()

        # project: user is manager
        self.project = Project(creator=self.user, name="asdf", description='project for fancy issues', name_short="PRJ")
        self.project.save()
        self.project.developer.add(self.user)
        self.project.manager.add(self.user)
        self.projiss1 = Issue(title="Issue for Proj1",
                              project=self.project,
                              kanbancol=self.project.kanbancol.first(),
                              type="Task"
                              )
        self.projiss1.save()
        self.projiss2 = Issue(title="Another Issue for Proj1",
                              project=self.project,
                              kanbancol=self.project.kanbancol.first(),
                              type="Bug"
                              )
        self.projiss2.save()
        # project2: user is developer
        self.project2 = Project(creator=self.user, name="2ndproj", name_short="PRJ2")
        self.project2.save()
        self.project2.developer.add(self.user)
        # project2: user is neither developer nor manager
        self.project3 = Project(creator=self.user, name="3rdproj", name_short="PRJ3")
        self.project3.save()
        self.proj2iss1 = Issue(title="Issue for Proj2",
                               project=self.project2,
                               kanbancol=self.project2.kanbancol.first(),
                               type="Bug"
                               )
        self.proj2iss1.save()

    def test_description_in_edit_is_necessary(self):
        driver = self.selenium
        driver.get('{}{}'.format(self.live_server_url, reverse('landing_page:home')))

        driver.find_element(By.CSS_SELECTOR, "span.glyphicon.glyphicon-search").click()
        driver.find_element(By.ID, "uinputxpr").clear()
        driver.find_element(By.ID, "uinputxpr").send_keys("Project.name_short ~~ \"PRJ\"")
        driver.find_element(By.XPATH, "//button[@type='submit']").click()
        driver.find_element(By.CSS_SELECTOR, "span.caret").click()
        driver.find_element(By.ID, "recent-searches-link").click()
        driver.find_element(By.CSS_SELECTOR, "button.btn.btn-link").click()
        driver.find_element(By.CSS_SELECTOR, "span.glyphicon.glyphicon-pencil").click()
        driver.find_element(By.ID, "id_description").clear()
        driver.find_element(By.ID, "id_description").send_keys("")
        driver.find_element(By.XPATH, "(//button[@type='submit'])[3]").click()

        self.assertIn("Edit filter", driver.page_source)

        search = Search.objects.first()
        self.assertEqual("Autosave", search.description)

    def test_change_search_permanment(self):
        driver = self.selenium
        driver.get('{}{}'.format(self.live_server_url, reverse('landing_page:home')))

        driver.find_element(By.CSS_SELECTOR, "span.glyphicon.glyphicon-search").click()
        driver.find_element(By.ID, "uinputxpr").clear()
        driver.find_element(By.ID, "uinputxpr").send_keys("Project.name_short ~~ \"PRJ\"")
        driver.find_element(By.XPATH, "//button[@type='submit']").click()
        driver.find_element(By.CSS_SELECTOR, "span.caret").click()
        driver.find_element(By.ID, "recent-searches-link").click()
        driver.find_element(By.CSS_SELECTOR, "button.btn.btn-link").click()
        self.assertEqual("Autosave", driver.find_element(By.CSS_SELECTOR, "#perSearch1 > td").text)
        driver.find_element(By.CSS_SELECTOR, "#perSearchForm1 > button.btn.btn-link").click()
        self.assertNotIn("Autosave", driver.page_source)

    def test_new_search(self):
        driver = self.selenium
        driver.get('{}{}'.format(self.live_server_url, reverse('landing_page:home')))

        driver.find_element(By.CSS_SELECTOR, "span.caret").click()
        driver.find_element(By.NAME, "expression").clear()
        driver.find_element(By.NAME, "expression").send_keys("Project.name_short ~~ \"PRJ\"")
        driver.find_element(By.CSS_SELECTOR, "button.btn.btn-default").click()
        self.assertEqual(self.project.name,
                         driver.find_element(By.CSS_SELECTOR,
                                             ".list-group > li:nth-child(2) > h4:nth-child(1) > a:nth-child(1)"
                                             ).text)
        self.assertEqual(self.project2.name,
                         driver.find_element(By.CSS_SELECTOR,
                                             ".list-group > li:nth-child(1) > h4:nth-child(1) > a:nth-child(1)"
                                             ).text)
        driver.find_element(By.CSS_SELECTOR, "span.caret").click()
        self.assertIn("Project.name_short ~~ &quot;PRJ&quot;", driver.page_source)
        driver.find_element(By.CSS_SELECTOR, "#search1 > button.btn.btn-default").click()
        self.assertEqual(self.project.name,
                         driver.find_element(By.CSS_SELECTOR,
                                             ".list-group > li:nth-child(2) > h4:nth-child(1) > a:nth-child(1)"
                                             ).text)
        self.assertEqual(self.project2.name,
                         driver.find_element(By.CSS_SELECTOR,
                                             ".list-group > li:nth-child(1) > h4:nth-child(1) > a:nth-child(1)"
                                             ).text)
        driver.find_element(By.CSS_SELECTOR, "span.caret").click()
        driver.find_element(By.NAME, "expression").clear()
        driver.find_element(By.NAME, "expression").send_keys("Issue.title ~~ \"Issue for Proj1\"")
        driver.find_element(By.CSS_SELECTOR, "button.btn.btn-default").click()
        self.assertEqual("(PRJ-2) Another Issue for Proj1",
                         driver.find_element(By.CSS_SELECTOR,
                                             ".list-group > li:nth-child(2) > h4:nth-child(1) > a:nth-child(1)"
                                             ).text)
        driver.find_element(By.CSS_SELECTOR, "a.dropdown-toggle").click()
        self.assertIn("Issue.title ~~ &quot;Issue for Proj1&quot;", driver.page_source)
        driver.find_element(By.NAME, "expression").clear()
        driver.find_element(By.NAME, "expression").send_keys("User.username == \"michgibtsnicht\"")
        driver.find_element(By.CSS_SELECTOR, "button.btn.btn-default").click()
        self.assertEqual("No items matching your query found", driver.find_element(By.CSS_SELECTOR, ".alert").text)
        driver.find_element(By.CSS_SELECTOR, "span.caret").click()
        driver.find_element(By.NAME, "expression").clear()
        driver.find_element(By.NAME, "expression").send_keys("Comment.invalidfield ~~ \"b\"")
        driver.find_element(By.CSS_SELECTOR, "button.btn.btn-default").click()
        self.assertEqual("No items matching your query found", driver.find_element(By.CSS_SELECTOR, ".alert").text)
        driver.find_element(By.CSS_SELECTOR, "span.glyphicon.glyphicon-search").click()
        driver.find_element(By.NAME, "expression").clear()
        driver.find_element(By.NAME, "expression").send_keys("()aaa")
        driver.find_element(By.CSS_SELECTOR, "button.btn.btn-default").click()
        self.assertEqual("No items matching your query found", driver.find_element(By.CSS_SELECTOR, ".alert").text)

        # full-text search
        driver.find_element(By.CSS_SELECTOR, "span.caret").click()
        driver.find_element(By.NAME, "expression").clear()
        driver.find_element(By.NAME, "expression").send_keys("iss")
        driver.find_element(By.CSS_SELECTOR, "button.btn.btn-default").click()

        self.assertIn("Issue",
                      driver.find_element(By.CSS_SELECTOR,
                                          "#filtertype_Issue > button:nth-child(4)"
                                          ).text)
        self.assertIn("Project",
                      driver.find_element(By.CSS_SELECTOR,
                                          "#filtertype_Project > button:nth-child(4)"
                                          ).text)
        self.assertIn("User",
                      driver.find_element(By.CSS_SELECTOR,
                                          "#filtertype_User > button:nth-child(4)"
                                          ).text)

        self.assertEqual(len(driver.find_element(By.CSS_SELECTOR,
                                                 ".col-md-9 ul"
                                                 ).text.split('\n')), 10)

        driver.find_element(By.CSS_SELECTOR, "#filtertype_Issue > button:nth-child(4)").click()

        # check that Issue button is now active
        self.assertEqual(driver.find_element(By.CSS_SELECTOR,
                                             "button.list-group-item:nth-child(3)"
                                             ).get_attribute('class'), 'list-group-item active')

        # check result list lengths for all buttons
        self.assertEqual(len(driver.find_element(By.CSS_SELECTOR,
                                                 ".col-md-9 ul"
                                                 ).text.split('\n')), 3)

        driver.find_element(By.CSS_SELECTOR, "#filtertype_Project > button:nth-child(4)").click()
        self.assertEqual(driver.find_element(By.CSS_SELECTOR,
                                             "button.list-group-item:nth-child(3)"
                                             ).get_attribute('class'), 'list-group-item active')
        self.assertEqual(driver.find_element(By.CSS_SELECTOR,
                                             "#filtertype_Issue > button:nth-child(4)"
                                             ).get_attribute('class'), 'list-group-item')

        self.assertEqual(len(driver.find_element(By.CSS_SELECTOR,
                                                 ".col-md-9 ul"
                                                 ).text.split('\n')), 1)

        driver.find_element(By.CSS_SELECTOR, "#filtertype_User > button:nth-child(4)").click()
        self.assertEqual(driver.find_element(By.CSS_SELECTOR,
                                             "button.list-group-item:nth-child(3)"
                                             ).get_attribute('class'), 'list-group-item active')
        self.assertEqual(driver.find_element(By.CSS_SELECTOR,
                                             "#filtertype_Project > button:nth-child(4)"
                                             ).get_attribute('class'), 'list-group-item')
        self.assertEqual(driver.find_element(By.CSS_SELECTOR,
                                             "#filtertype_Issue > button:nth-child(4)"
                                             ).get_attribute('class'), 'list-group-item')

        self.assertEqual(len(driver.find_element(By.CSS_SELECTOR,
                                                 ".col-md-9 ul"
                                                 ).text.split('\n')), 1)

        # disable currently selected button and check result list size and highlighting
        driver.find_element(By.CSS_SELECTOR, "button.list-group-item:nth-child(3)").click()
        self.assertEqual(len(driver.find_element(By.CSS_SELECTOR,
                                                 ".col-md-9 ul"
                                                 ).text.split('\n')), 10)
        self.assertEqual(driver.find_element(By.CSS_SELECTOR,
                                             "#filtertype_User > button:nth-child(4)"
                                             ).get_attribute('class'), 'list-group-item')

        # test empty search string (should fail)
        driver.find_element(By.CSS_SELECTOR, "span.caret").click()
        driver.find_element(By.NAME, "expression").clear()
        driver.find_element(By.NAME, "expression").send_keys("")
        driver.find_element(By.CSS_SELECTOR, "button.btn.btn-default").click()

        self.assertIn('Please search for at least three characters', driver.page_source)

        # should always fail with less than three chars
        driver.find_element(By.CSS_SELECTOR, "span.caret").click()
        driver.find_element(By.NAME, "expression").clear()
        driver.find_element(By.NAME, "expression").send_keys("aa")
        driver.find_element(By.CSS_SELECTOR, "button.btn.btn-default").click()

        self.assertIn('Please search for at least three characters', driver.page_source)

        # test marking search persistent
        qstring = 'Issue.type == "Bug"'
        q = SearchFrontend.query(qstring, self.user)
        self.assertEqual(len(q), 2)
        driver.find_element(By.CSS_SELECTOR, "span.caret").click()
        driver.find_element(By.ID, "recent-searches-link").click()
        driver.find_element(By.CSS_SELECTOR, "button.btn.btn-link").click()
        driver.find_element(By.CSS_SELECTOR,
                            "div.col-md-6:nth-child(2) > div:nth-child(1) > table:nth-child(2) >" +
                            " tbody:nth-child(1) > tr:nth-child(1) > td:nth-child(2) > a:nth-child(1)").click()
        self.assertEqual(driver.find_element(By.ID, "id_searchexpression").get_attribute("value"), qstring)
        driver.find_element(By.ID, "id_description").clear()
        driver.find_element(By.ID, "id_description").send_keys("Fancy filter")
        self.assertEqual(Search.objects.get(searchexpression=qstring).persistent, True)

        driver.find_element(By.CSS_SELECTOR, ".select2-selection__rendered").click()
        time.sleep(1)
        for i in driver.find_elements(By.CSS_SELECTOR, '#select2-id_shared_with-results li'):
            if i.text == self.project.name:
                i.click()
                break
        driver.find_element(By.CSS_SELECTOR, ".save").click()
        driver.find_element(By.LINK_TEXT, "Projects").click()
        driver.find_element(By.LINK_TEXT, self.project.name).click()
        driver.find_element(By.LINK_TEXT, "Settings").click()
        driver.find_element(By.LINK_TEXT, "Search filters").click()
        elem = driver.find_element(By.CSS_SELECTOR, ".btn-link")
        self.assertEqual(elem.text, "Fancy filter")
        elem.click()
        self.assertEqual(len(driver.find_element(By.CSS_SELECTOR, ".col-md-12 ul").text.split("\n")), 3)

        # test delete
        driver.get('{}{}'.format(self.live_server_url, reverse('search:advanced')))
        driver.find_element(By.CSS_SELECTOR,
                            "div.col-md-6:nth-child(2) > div:nth-child(1) > " +
                            "table:nth-child(2) > tbody:nth-child(1) > tr:nth-child(1) > td:nth-child(3) > " +
                            "form:nth-child(1) > button:nth-child(3)").click()
        self.assertEqual(len(Search.objects.filter(searchexpression=qstring)), 0)

    def test_search_combine_proj_and_type_filter(self):
        # TODO TESTCASE test_search_combine_proj_and_type_filter
        # TODO TESTCASE verify both amount illustrations of results: with and without active filter
        pass

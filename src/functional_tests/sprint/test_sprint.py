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
import datetime
import time

from django.contrib.auth import get_user_model
from issue.models import Issue
from kanbancol.models import KanbanColumn
from project.models import Project


# TODO we might wanna test the href-links on those pages
class SprintTest(SeleniumTestCase):

    def setUp(self):
        self.user = get_user_model().objects.create_user('a', 'b', 'c')
        self.project = Project(name="Fancy Project", name_short="FYP", description="Fancy description",
                               creator=self.user)
        self.project.save()
        self.project.developer.add(self.user)
        self.project2 = Project(name="plain Project", name_short="plai", creator=self.user)
        self.project2.save()
        self.project2.developer.add(self.user)

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
        # TODO backlog
        # TODO edit sprint
        # TODO sprintboard
        pass

    def test_create_sprint(self):
        # TODO TESTCASE
        pass

    def test_edit_sprint(self):
        # TODO TESTCASE
        pass

    def test_assign_issue_to_sprint(self):
        # TODO TESTCASE
        pass

    def test_remove_issue_form_sprint(self):
        # TODO TESTCASE
        pass

    def test_start_sprint(self):
        # TODO TESTCASE
        pass

    def test_stop_sprint(self):
        # TODO TESTCASE
        pass

    def test_sprintboard(self):
        # TODO TESTCASE (switch cols)
        pass

    def test_backlog(self):
        # TODO TESTCASE
        pass

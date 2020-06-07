"""
Iguana (c) by Marc Ammon, Moritz Fickenscher, Lukas Fridolin,
Michael Gunselmann, Katrin Raab, Christian Strate

Iguana is licensed under a
Creative Commons Attribution-ShareAlike 4.0 International License.

You should have received a copy of the license along with this
work. If not, see <http://creativecommons.org/licenses/by-sa/4.0/>.
"""
import base64
from django.test import TestCase
from django.urls import reverse

from api.views import UserViewSet, ProjectViewSet
from django.contrib.auth import get_user_model, login
from project.models import Project
from common.testcases.generic_testcase_helper import view_and_template, redirect_to_login_and_login_required


class ApiViewsTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        # NOTE: if you modify those elements they need to be created in setUp(), instead of here
        cls.user = get_user_model().objects.create_user('a', 'a@a.com', 'a1234568')
        cls.project = Project(creator=cls.user, name_short='asdf')

    def setUp(self):
        self.client.force_login(self.user)
        # NOTE: these elements get modified by some testcases, so they should NOT be created in setUpTestData()
        self.user_auth = 'Basic ' + base64.b64encode('a:a12345678'.encode()).decode()

    def test_view_and_template(self):
        # TODO TESTCASE api view and template
        #      use view_and_template()
        # TODO which views?
        #      - UserViewSet
        # view_and_template(self, UserViewSet, '', 'api:users')
        view_and_template(self, ProjectViewSet, None, 'api:project-detail',
                          address_kwargs={'name_short': self.project.name_short})
        #      - 'timelogs'
        #      - 'notifications'
        #      - 'issues'
        #      - 'project'
        #      - 'project_timelogs'
        #      - 'project_issues'
        #      - 'project_sprints'
        #      - 'project_issues_comments'
        #      - 'project_issues_timelogs'
        #      - ...

        pass

    def test_redirect_to_login_and_login_required(self):
        self.client.logout()
        # TODO TESTCASE api redirect to login and login required
        #      redirect_to_login_and_login_required()
        # TODO which views?
        #      - UserViewSet
        #      - 'timelogs'
        #      - 'notifications'
        #      - 'issues'
        #      - 'project'
        #      - 'project_timelogs'
        #      - 'project_issues'
        #      - 'project_sprints'
        #      - 'project_issues_comments'
        #      - 'project_issues_timelogs'
        #      - ...
        pass

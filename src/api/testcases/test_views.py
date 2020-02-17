"""
Iguana (c) by Marc Ammon, Moritz Fickenscher, Lukas Fridolin,
Michael Gunselmann, Katrin Raab, Christian Strate

Iguana is licensed under a
Creative Commons Attribution-ShareAlike 4.0 International License.

You should have received a copy of the license along with this
work. If not, see <http://creativecommons.org/licenses/by-sa/4.0/>.
"""
from django.test import TestCase
from django.urls import reverse

from invite_users.views import InviteUserView, SuccessView
from user_management.views import LoginView
from django.contrib.auth import get_user_model, login
from common.testcases.generic_testcase_helper import view_and_template, redirect_to_login_and_login_required


class ApiViewsTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        # NOTE: if you modify this element it needs to be created in setUp, instead of here
        cls.user = get_user_model().objects.create_user('a', 'a@a.com', 'a1234568')

    def setUp(self):
        self.client.force_login(self.user)

    def test_view_and_template(self):
        # TODO TESTCASE api view and template
        #      use view_and_template()
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

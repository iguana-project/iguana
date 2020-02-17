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

from project.models import Project
from issue.models import Issue
from discussion.views import DiscussionsView, SeenView, MuteView, FollowView
from user_management.views import LoginView
from django.contrib.auth import get_user_model, login
from common.testcases.generic_testcase_helper import view_and_template, redirect_to_login_and_login_required


class DiscussionGenericTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        # NOTE: if you modify this element it needs to be created in setUp(), instead of here
        cls.user = get_user_model().objects.create_user('a', 'a@a.com', 'a1234568')

    def setUp(self):
        self.client.force_login(self.user)
        # NOTE: these elements get modified by some testcases, so this should NOT be created in setUpTestData()
        self.project = Project(creator=self.user, name_short='PRJ')
        self.project.save()
        self.issue = Issue(title="Test-Issue", project=self.project, type="Bug")
        self.issue.save()

    def test_view_and_template(self):
        # TODO TESTCASE discussion-test view and templates
        # DiscussionsView
        view_and_template(self, DiscussionsView, 'discussions.html', 'discussion:list')
        # SeenView
        # TODO requires post request
        # view_and_template(self, SeenView, 'discussions.html', 'discussion:seen',
        #                   address_kwargs={'project': self.project.name_short})
        # MuteView
        # view_and_template(self, MuteView, 'issue/issue_detail_view.html', 'discussion:mute',
        #                   address_kwargs={'project': self.project.name_short, 'sqn_i': self.issue.number})
        #      - FollowView - follow
        # view_and_template(self, FollowView, 'issue/issue_detail_view.html', 'discussion:follow',
        #                   address_kwargs={'project': self.project.name_short, 'sqn_i': self.issue.number})

    def test_redirect_to_login_and_login_required(self):
        self.client.logout()
        # DiscussionsView
        redirect_to_login_and_login_required(self, 'discussion:list')
        # SeenView
        redirect_to_login_and_login_required(self, 'discussion:seen',
                                             address_kwargs={'project': self.project.name_short})
        # MuteView
        redirect_to_login_and_login_required(self, 'discussion:mute',
                                             address_kwargs={'project': self.project.name_short,
                                                             'sqn_i': self.issue.number})
        # FollowView
        redirect_to_login_and_login_required(self, 'discussion:follow',
                                             address_kwargs={'project': self.project.name_short,
                                                             'sqn_i': self.issue.number})

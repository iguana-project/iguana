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
        # NOTE: if you modify these elements they need to be created in setUp(), instead of here
        cls.user = get_user_model().objects.create_user('a', 'a@a.com', 'a1234568')

    def setUp(self):
        self.client.force_login(self.user)
        # NOTE: these elements get modified by some testcases, so they should NOT be created in setUpTestData()
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

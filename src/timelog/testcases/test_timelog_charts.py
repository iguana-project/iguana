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
from django.utils import timezone

from timelog.views import TimelogGetActivityDataView, TimelogD3View
from project.models import Project
from issue.models import Issue
from timelog.models import Timelog
from kanbancol.models import KanbanColumn
from django.contrib.auth import get_user_model
from common.testcases.generic_testcase_helper import view_and_template, redirect_to_login_and_login_required


# some fake tests for coverage, todo: QUnit, javascript unit testing
class TimelogChartsTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        # NOTE: if you modify these elements they need to be created in setUp(), instead of here
        cls.user = get_user_model().objects.create_user('test', 'test@testing.com', 'test1234')
        cls.project = Project(creator=cls.user, name_short='PRJ')
        cls.project.save()
        cls.project.developer.add(cls.user)
        cls.kanbancol = KanbanColumn(project=cls.project, position=4, name='test')
        cls.kanbancol.save()
        cls.issue = Issue(project=cls.project, due_date='2016-12-16', kanbancol=cls.kanbancol, storypoints='3')
        cls.issue.save()
        cls.issue2 = Issue(project=cls.project, due_date='2016-12-16', kanbancol=cls.kanbancol, storypoints='3')
        cls.time = timezone.now().replace(microsecond=100000)
        cls.timestamp = cls.time.timestamp()

    def setUp(self):
        self.client.force_login(self.user)
        # NOTE: these elements get modified by some testcases, so they should NOT be created in setUpTestData()

    def test_view_and_template(self):
        # activity_chart
        view_and_template(self, TimelogGetActivityDataView, 'timelog/timelog_activity.html', 'timelog:activity')

        # last seven day chart
        view_and_template(self, TimelogD3View, 'timelog/timelog_d3.html', 'timelog:d3')
        # TODO TESTCASE see invite_users
        #      use view_and_template()
        # TODO which views?
        #      - ...
        pass

    def test_redirect_to_login_and_login_required(self):
        self.client.logout()
        # TODO TESTCASE see invite_users
        #      redirect_to_login_and_login_required()
        # TODO which views?
        #      - timelog:activity
        #      - timelog:d3
        #      - ...
        pass

    def test_user_passes_test_mixin(self):
        # TODO TESTCASE
        # TODO maybe only devs of a project shall be able to see this?
        # TODO activity
        # TODO d3
        pass

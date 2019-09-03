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
        # NOTE: if you modify those elements they need to be created in setUp, instead of here
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

    def test_view_and_template(self):
        # activity_chart
        view_and_template(self, TimelogGetActivityDataView, 'timelog/timelog_activity.html', 'timelog:activity')

        # last seven day chart
        view_and_template(self, TimelogD3View, 'timelog/timelog_d3.html', 'timelog:d3')

    def test_redirect_to_login_and_login_required(self):
        # TODO TESTCASE
        # TODO activity
        # TODO d3
        pass

    def test_user_passes_test_mixin(self):
        # TODO TESTCASE
        # TODO maybe only devs of a project shall be able to see this?
        # TODO activity
        # TODO d3
        pass

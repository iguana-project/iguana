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
from datetime import timedelta
import datetime

from project.models import Project
from kanbancol.models import KanbanColumn
from tag.models import Tag
from issue.models import Issue
from sprint.models import Sprint
from timelog.models import Timelog
from django.contrib.auth import get_user_model

from archive.views import ArchivedIssuesView
from common.testcases.generic_testcase_helper import view_and_template, redirect_to_login_and_login_required


class CreateArchiveTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        # NOTE: if you modify these elements they need to be created in setUp(), instead of here
        cls.user = get_user_model().objects.create_user('a', 'b', 'c')

    def setUp(self):
        self.client.force_login(self.user)
        # NOTE: these elements get modified by some testcases, so they should NOT be created in setUpTestData()
        self.project = Project(creator=self.user, name_short='PRJ')
        self.project.save()
        self.project.manager.add(self.user)
        self.project.developer.add(self.user)

    def test_view_and_template(self):
        view_and_template(self, ArchivedIssuesView,  'archive/archived_issues_view.html',
                          'archive:archive', address_kwargs={'project': 'PRJ'})

    def test_redirect_to_login_and_login_required(self):
        self.client.logout()
        redirect_to_login_and_login_required(self, 'archive:archive', address_kwargs={'project': 'PRJ'})

    def test_sprints_and_issues_in_archive_view(self):
        newsprint = Sprint(project=self.project)
        newsprint.save()
        startedsprint = Sprint(project=self.project,
                               startdate=datetime.datetime.now())
        startedsprint.save()
        stoppedsprint = Sprint(project=self.project,
                               startdate=datetime.datetime.now(),
                               enddate=datetime.datetime.now())
        stoppedsprint.save()
        wrongsprint = Sprint(project=self.project,
                             enddate=datetime.datetime.now())
        wrongsprint.save()
        issueinnew = Issue(title="boo", project=self.project,
                           sprint=newsprint, archived=True)
        issueinnew.save()
        issueinstarted = Issue(title="coo", project=self.project,
                               sprint=startedsprint, archived=True)
        issueinstarted.save()
        issueinstopped = Issue(title="doo", project=self.project,
                               sprint=stoppedsprint, archived=True)
        issueinstopped.save()
        issueinwrong = Issue(title="foo", project=self.project,
                             sprint=wrongsprint, archived=True)
        issueinwrong.save()
        issueinno = Issue(title="goo", project=self.project,
                          archived=True)
        issueinno.save()

        response = self.client.get(reverse('archive:archive',
                                   kwargs={'project': self.project.name_short}))
        self.assertNotIn(issueinnew, response.context['archived_issues_without_sprint'])
        self.assertNotIn(issueinwrong, response.context['archived_issues_without_sprint'])
        self.assertNotIn(issueinstopped, response.context['archived_issues_without_sprint'])
        self.assertNotIn(issueinstarted, response.context['archived_issues_without_sprint'])
        self.assertIn(issueinno, response.context['archived_issues_without_sprint'])
        self.assertEqual(response.context['sprints_sorted'].all()[0], wrongsprint)
        self.assertEqual(response.context['sprints_sorted'].all()[1], stoppedsprint)
        self.assertEqual(response.context['sprints_sorted'].all()[2], startedsprint)
        self.assertEqual(response.context['sprints_sorted'].all()[3], newsprint)

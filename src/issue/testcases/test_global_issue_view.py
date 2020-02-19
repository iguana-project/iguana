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
from common.models import Filter
from django.contrib.auth import get_user_model
from common.testcases import generic_testcase_helper


class CreateGlobalTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        # NOTE: if you modify these elements they need to be created in setUp(), instead of here
        cls.user = get_user_model().objects.create_user('a', 'b', 'c')
        cls.user2 = get_user_model().objects.create_user('d', 'e', 'f')

    def setUp(self):
        self.client.force_login(self.user)
        # NOTE: these elements get modified by some testcases, so they should NOT be created in setUpTestData()
        self.project = Project(creator=self.user, name_short='PRJ')
        self.project.save()
        self.project.manager.add(self.user)
        self.project.developer.add(self.user)
        self.project2 = Project(creator=self.user, name_short='TP')
        self.project2.save()
        self.project2.manager.add(self.user)
        self.project2.developer.add(self.user)
        self.column = KanbanColumn(name='Column', position=4, project=self.project)
        self.column.save()

    # helper function
    def create_some_issues(self):
        col = KanbanColumn.objects.filter(project=self.project)
        col2 = KanbanColumn.objects.filter(project=self.project2)
        iss = []
        iss.append(Issue(title='asd', kanbancol=col.get(pk=1), priority=0, type='Bug', project=self.project))
        iss.append(Issue(title='asd2', kanbancol=col.get(pk=2), priority=1, type='Story', project=self.project))
        iss.append(Issue(title='asd3', kanbancol=col.get(pk=3), priority=2, type='Task', project=self.project))
        iss.append(Issue(title='asd4', kanbancol=col.get(pk=3), priority=3, archived=True, project=self.project))
        iss.append(Issue(title='asd5', kanbancol=col2.first(), priority=4, project=self.project2))
        for issue in iss:
            issue.save()
            issue.assignee.add(self.user)
        return iss

    def test_view_and_template(self):
        # TODO TESTCASE simplify testcase with view_and_template()
        #      view_and_template(self, , , )
        # TODO which views?
        #      - url(r'^$', views.IssueGlobalView.as_view(), name='issue_global_view'),
        #      - url(r'^project/'+project_pattern+r'issue/', include([
        #      -   url(r'assigntome/?$', views.AssignIssueToMeView.as_view(), name='assigntome',),
        #      -   url(r'^rmfromme/?$', views.RemoveIssueFromMeView.as_view(), name='rmfromme',),
        #      -   url(r'^setkanbancol/?$', views.AddIssueToKanbancolView.as_view(), name='setkanbancol',),
        #      -   url(r'^archivecol/?$', views.ArchiveMultipleIssueView.as_view(), name='archivecol',),
        #      -   url(r'^archiveissue/?$', views.ArchiveSingleIssueView.as_view(), name='archiveissue',),
        #      -   url(r'^unarchiveissue/?$', views.UnArchiveSingleIssueView.as_view(), name='unarchiveissue',),
        #      - url(r'^(?P<sqn_i>[0-9]+)/', include([
        #      -     url(r'^delete/?$', views.IssueDeleteView.as_view(), name='delete'),
        #      - ]))
        #      - url(r'^(?P<sqn_i>[0-9]+)/', include([
        #      -    url(r'^punch/?$', tl_views.PunchView.as_view(), name='punch'),
        pass

    def test_redirect_to_login_and_loign_required(self):
        # TODO TESTCASE simplify testcase with view_and_template()
        #      redirect_to_login_and_login_required(self, address_pattern, address_kwargs=None, get_kwargs=None,
        #                                 alternate_error_message=None):
        # TODO which views?
        #      - url(r'^$', views.IssueGlobalView.as_view(), name='issue_global_view'),
        #      - url(r'^project/'+project_pattern+r'issue/', include([
        #      -   url(r'assigntome/?$', views.AssignIssueToMeView.as_view(), name='assigntome',),
        #      -   url(r'^rmfromme/?$', views.RemoveIssueFromMeView.as_view(), name='rmfromme',),
        #      -   url(r'^setkanbancol/?$', views.AddIssueToKanbancolView.as_view(), name='setkanbancol',),
        #      -   url(r'^archivecol/?$', views.ArchiveMultipleIssueView.as_view(), name='archivecol',),
        #      -   url(r'^archiveissue/?$', views.ArchiveSingleIssueView.as_view(), name='archiveissue',),
        #      -   url(r'^unarchiveissue/?$', views.UnArchiveSingleIssueView.as_view(), name='unarchiveissue',),
        #      - url(r'^(?P<sqn_i>[0-9]+)/', include([
        #      -     url(r'^delete/?$', views.IssueDeleteView.as_view(), name='delete'),
        #      - ]))
        #      - url(r'^(?P<sqn_i>[0-9]+)/', include([
        #      -    url(r'^punch/?$', tl_views.PunchView.as_view(), name='punch'),
        pass

    def test_issue_properties(self):
        issues = self.create_some_issues()

        # archived issue is not in context
        response = self.client.get(reverse('issue:issue_global_view'))
        self.assertIn(issues[0], response.context['issues'].object_list)
        self.assertNotIn(issues[3], response.context['issues'].object_list)

        # done issue is not in context
        response = self.client.get(reverse('issue:issue_global_view'))
        self.assertNotIn(issues[2], response.context['issues'].object_list)

        # archived/done issue is not in context, done issue is in context
        response = self.client.get(reverse('issue:issue_global_view'))
        self.assertIn(issues[0], response.context['issues'].object_list)
        self.assertIn(issues[1], response.context['issues'].object_list)
        self.assertIn(issues[4], response.context['issues'].object_list)
        self.assertNotIn(issues[3], response.context['issues'].object_list)
        self.assertNotIn(issues[2], response.context['issues'].object_list)

        # filter project
        response = self.client.get(reverse('issue:issue_global_view')+'?show_done=false'+'&project=PRJ')

        # issue from second project not in context
        self.assertNotIn(issues[4], response.context['issues'].object_list)
        # not done issues from first project in context
        self.assertEqual(2, len(response.context['issues'].object_list))

        # filter not existing project
        response = self.client.get(reverse('issue:issue_global_view')+'?show_done=false'+'&project=PRJ2')
        self.assertIn(issues[4], response.context['issues'].object_list)
        self.assertEqual(3, len(response.context['issues'].object_list))

        # filter in running sprint
        sprint = Sprint(project=self.project)
        sprint.save()
        issues[0].sprint = sprint
        issues[0].save()
        response = self.client.get(reverse('issue:issue_global_view') + '?show_done=true' +
                                   '&project=PRJ&sprint_only=true')
        self.assertEqual(0, len(response.context['issues'].object_list))
        sprint.set_active()
        response = self.client.get(reverse('issue:issue_global_view') + '?show_done=true' +
                                   '&project=PRJ&sprint_only=true')
        self.assertEqual(1, len(response.context['issues'].object_list))
        self.assertIn(issues[0], response.context['issues'].object_list)
        sprint.set_inactive()
        response = self.client.get(reverse('issue:issue_global_view') + '?show_done=true' +
                                   '&project=PRJ&sprint_only=true')
        self.assertEqual(0, len(response.context['issues'].object_list))

        # order_by title
        response = self.client.get(reverse('issue:issue_global_view') + '?show_done=true' +
                                   '&order_by=title' + '&project=PRJ')
        self.assertEqual(issues[0], response.context['issues'].object_list.pop(0))
        response = self.client.get(reverse('issue:issue_global_view') + '?show_done=true' +
                                   '&order_by=title' + '&project=PRJ&reverse=true')
        self.assertEqual(issues[2], response.context['issues'].object_list.pop(0))

        # order_by priority
        response = self.client.get(reverse('issue:issue_global_view') + '?show_done=true' +
                                   '&order_by=priority&reverse=false')
        self.assertEqual(issues[4], response.context['issues'].object_list.pop(0))
        response = self.client.get(reverse('issue:issue_global_view') + '?show_done=true' +
                                   '&order_by=priority&reverse=true')
        self.assertEqual(issues[0], response.context['issues'].object_list.pop(0))

        # order_by type
        response = self.client.get(reverse('issue:issue_global_view') + '?show_done=true' +
                                   '&order_by=type&project=PRJ&reverse=false')
        self.assertEqual(3, len(response.context['issues'].object_list))
        self.assertEqual(issues[0], response.context['issues'].object_list.pop(0))
        self.assertEqual(issues[2], response.context['issues'].object_list.pop(1))
        response = self.client.get(reverse('issue:issue_global_view') + '?show_done=true' +
                                   '&order_by=type&reverse=true&project=PRJ')
        self.assertEqual(3, len(response.context['issues'].object_list))
        self.assertEqual(issues[2], response.context['issues'].object_list.pop(0))
        self.assertEqual(issues[0], response.context['issues'].object_list.pop(1))

        # order_by status
        response = self.client.get(reverse('issue:issue_global_view') + '?show_done=true' +
                                   '&order_by=status&project=PRJ')
        self.assertEqual(3, len(response.context['issues'].object_list))
        self.assertEqual(issues[0], response.context['issues'].object_list.pop(0))
        self.assertEqual(issues[2], response.context['issues'].object_list.pop(1))
        response = self.client.get(reverse('issue:issue_global_view') + '?show_done=true' +
                                   '&order_by=status&reverse=true&project=PRJ')
        self.assertEqual(3, len(response.context['issues'].object_list))
        self.assertEqual(issues[0], response.context['issues'].object_list.pop(0))
        self.assertEqual(issues[2], response.context['issues'].object_list.pop(1))

        # test pagination PageNotInteger exception
        response = self.client.get(reverse('issue:issue_global_view') +
                                   '?page=asd' + '&show_done=true', follow=True)
        self.assertEqual(4, len(response.context['issues'].object_list))

        # test pagination EmptyPage exception
        response = self.client.get(reverse('issue:issue_global_view') +
                                   '?page=5' + '&show_done=true', follow=True)
        self.assertEqual(4, len(response.context['issues'].object_list))

    def test_save_filters(self):
        issues = self.create_some_issues()
        vals = {
                'typ': 'issue_global_view',
        }
        response = self.client.get(reverse('issue:issue_global_view') + '?show_done=true' +
                                   '&order_by=status&reverse=true&project=PRJ')
        string = response.request.get('QUERY_STRING')
        vals.update({'string': string, 'name': 'asdf'})
        response = self.client.post(reverse('common:create_filter'), vals, follow=True)
        self.assertEqual(self.user.filters.count(), 1)
        self.assertContains(response, 'asdf')
        vals.update({'string': string, 'name': 'ghjk'})
        response = self.client.post(reverse('common:create_filter'), vals, follow=True)
        self.assertEqual(self.user.filters.count(), 1)
        vals.update({'string': '?order_by=priority', 'name': 'asdf'})
        response = self.client.post(reverse('common:create_filter'), vals, follow=True)
        self.assertEqual(self.user.filters.count(), 1)
        vals.update({'typ': 'lalala', 'name': 'yoyo'})
        response = self.client.post(reverse('common:create_filter'), vals, follow=True)
        self.assertEqual(self.user.filters.count(), 2)
        self.assertNotContains(response, 'yoyo')

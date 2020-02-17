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
import datetime
import os

from sprint.views import SprintboardView, StartSprintView, StopSprintView, SprintEditView, ToggleIssueToFromSprintView
from backlog.views import BacklogListView
from project.models import Project
from kanbancol.models import KanbanColumn
from issue.models import Issue
from sprint.models import Sprint
from django.contrib.auth import get_user_model
from common.testcases.generic_testcase_helper import view_and_template, redirect_to_login_and_login_required


class SprintTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        # NOTE: if you modify this element it needs to be created in setUp(), instead of here
        cls.user = get_user_model().objects.create_user('a', 'b', 'c')

    def setUp(self):
        self.client.force_login(self.user)

        # NOTE: this element gets modified by some of those tests, so this shall NOT be created in setUpTestData()
        self.project = Project(creator=self.user, name_short='PRJ')
        self.project.save()
        self.project.manager.add(self.user)

        self.sprint = Sprint(project=self.project)
        self.sprint.save()

    def test_view_and_template(self):
        # SprintboardView
        view_and_template(self, SprintboardView, 'sprint/sprintboard.html', 'sprint:sprintboard',
                          address_kwargs={'project': self.project.name_short})
        # NewSprint doesn't render a template but redirects to BacklogListView
        view_and_template(self, BacklogListView, 'backlog/backlog_list.html', 'sprint:newsprint',
                          address_kwargs={'project': self.project.name_short})
        # StartSprint doesn't render a template but redirects to BacklogListView
        # TODO this requires a post request
        # view_and_template(self, StartSprintView, 'backlog/backlog_list.html', 'sprint:startsprint',
        #                   address_kwargs={'project': self.project.name_short, 'sqn_s': self.sprint.seqnum})
        # StopSprintView
        view_and_template(self, StopSprintView, 'sprint/sprint_finish.html', 'sprint:stopsprint',
                          address_kwargs={'project': self.project.name_short, 'sqn_s': self.sprint.seqnum})

        # SprintEditView
        view_and_template(self, SprintEditView, 'sprint/sprint_edit.html', 'sprint:editsprint',
                          address_kwargs={'project': self.project.name_short, 'sqn_s': self.sprint.seqnum})
        # ToggleIssueToFromSprintView doesn't render a template but redirects to BacklogListView
        # TODO this requires a post request
        # view_and_template(self, ToggleIssueToFromSprintView, 'backlog/backlog_list.html', 'sprint:assigntosprint',
        #                   address_kwargs={'project': self.project.name_short})

    def test_redirect_to_login_and_login_required(self):
        self.client.logout()
        # Sprintboard
        redirect_to_login_and_login_required(self, 'sprint:sprintboard',
                                             address_kwargs={'project': self.project.name_short})
        # NewSprint
        redirect_to_login_and_login_required(self, 'sprint:newsprint',
                                             address_kwargs={'project': self.project.name_short})
        # StartSprint
        redirect_to_login_and_login_required(self, 'sprint:startsprint',
                                             address_kwargs={'project': self.project.name_short,
                                                             'sqn_s': self.sprint.seqnum})
        # StopSprint
        redirect_to_login_and_login_required(self, 'sprint:stopsprint',
                                             address_kwargs={'project': self.project.name_short,
                                                             'sqn_s': self.sprint.seqnum})
        # SprintEditView
        redirect_to_login_and_login_required(self, 'sprint:editsprint',
                                             address_kwargs={'project': self.project.name_short,
                                                             'sqn_s': self.sprint.seqnum})
        # ToggleIssueToFromSprintView
        redirect_to_login_and_login_required(self, 'sprint:assigntosprint',
                                             address_kwargs={'project': self.project.name_short})

    def test_user_passes_test_mixin(self):
        # TODO TESTCASE
        # TODO NewSprint
        # TODO StartSprint
        # TODO StopSprint
        # TODO Sprint_Edit_View
        pass

    def test_flags(self):
        kanbancol = KanbanColumn(name='Column', position=1, project=self.project)
        kanbancol.save()
        issue = Issue(title="Test-Issue", kanbancol=kanbancol, project=self.project, type="Bug", sprint=self.sprint)
        issue.save()
        self.assertEqual(issue.was_in_sprint, False)

        response = self.client.post(
                reverse('sprint:stopsprint', kwargs={'project': self.project.name_short, 'sqn_s': self.sprint.seqnum}))
        self.assertEqual(Issue.objects.get(pk=issue.pk).was_in_sprint, True)

        issue.save()  # unset the flag
        self.assertEqual(issue.was_in_sprint, False)

    def test_sprint_functions(self):
        # sprint is new sprint
        self.assertTrue(self.sprint in Sprint.objects.get_new_sprints())
        self.assertFalse(self.sprint in Sprint.objects.get_current_sprints())
        self.assertFalse(self.sprint in Sprint.objects.get_old_sprints())

        # set sprint active
        self.sprint.set_active()
        self.assertTrue(self.sprint.is_active)

        # sprint is new current sprint
        self.assertFalse(self.sprint in Sprint.objects.get_new_sprints())
        self.assertTrue(self.sprint in Sprint.objects.get_current_sprints())
        self.assertFalse(self.sprint in Sprint.objects.get_old_sprints())

        # done and undone issue to put back in backlog
        kanbancoldone = KanbanColumn.objects.get(type='Done', project=self.project)
        kanbancolprogress = KanbanColumn.objects.get(type='InProgress', project=self.project)
        issuedone = Issue(title="Test-Issue",
                          kanbancol=kanbancoldone,
                          project=self.project,
                          type="Bug",
                          sprint=self.sprint)
        issuedone.save()
        issueprogress = Issue(title="Test-Issue",
                              kanbancol=kanbancolprogress,
                              project=self.project,
                              type="Bug",
                              sprint=self.sprint)
        issueprogress.save()

        # set sprint inactive
        issueleft = self.sprint.set_inactive()
        self.assertTrue(self.sprint.is_inactive())
        issuedone.refresh_from_db()
        issueprogress.refresh_from_db()

        # issues are right archived and assigned
        self.assertTrue(issueleft)
        self.assertTrue(issuedone.archived)
        self.assertFalse(issueprogress.archived)
        self.assertIsNotNone(issuedone.sprint)
        self.assertIsNone(issueprogress.sprint)
        self.assertTrue(issueprogress.was_in_sprint)

        # sprint is new old sprint
        self.assertFalse(self.sprint in Sprint.objects.get_new_sprints())
        self.assertFalse(self.sprint in Sprint.objects.get_current_sprints())
        self.assertTrue(self.sprint in Sprint.objects.get_old_sprints())

    def test_create_sprint(self):
        self.assertNotEqual(self.sprint.seqnum, -1)
        nextseqnum = self.sprint.seqnum + 1
        n = Sprint.objects.count() + 1
        response = self.client.get(reverse('sprint:newsprint',
                                           kwargs={'project': self.project.name_short}
                                           ))

        self.assertRedirects(response, reverse('backlog:backlog',
                             kwargs={'project': self.project.name_short, 'sqn_s': nextseqnum}))
        response = self.client.get(response['location'])
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Sprint.objects.count(), n)

    def test_start_and_stop_sprint(self):
        # self.sprint should not have started
        self.assertNotEqual(self.sprint.seqnum, -1)
        project = Project(creator=self.user, name_short='APF')
        project.save()
        project.manager.add(self.user)

        n = Sprint.objects.get_new_sprints().count()
        sprint = Sprint(project=project)
        sprint.save()
        self.assertEqual(Sprint.objects.get_new_sprints().count(), (n+1))
        self.assertTrue(sprint in Sprint.objects.get_new_sprints())
        self.assertFalse(sprint in Sprint.objects.get_current_sprints())
        self.assertFalse(sprint in Sprint.objects.get_old_sprints())
        self.assertIsNone(project.currentsprint)

        # columns and issues for testing archiving function
        kanbancol3 = KanbanColumn.objects.get(name='Todo', project=project)
        kanbancol3.type = 'Done'
        kanbancol3.save()
        kanbancol2 = KanbanColumn.objects.get(name='In Progress', project=project)
        kanbancol1 = KanbanColumn.objects.get(name='Done', project=project)
        kanbancol1.type = 'ToDo'
        kanbancol1.save()

        issue = Issue(title="Test-Issue", kanbancol=kanbancol1, project=project, type="Bug", sprint=sprint)
        issue.save()
        issue2 = Issue(title="Test-Issue2", kanbancol=kanbancol2, project=project, type="Bug", sprint=sprint)
        issue2.save()
        issue3 = Issue(title="Test-Issue3", kanbancol=kanbancol3, project=project, type="Bug", sprint=sprint)
        issue3.save()
        issue4 = Issue(title="Test-Issue4", kanbancol=kanbancol3, project=project, type="Bug")
        issue4.save()

        # issues (except issue4) should be in not started sprint
        self.assertFalse(issue in Issue.objects.without_sprint())
        self.assertFalse(issue in Issue.objects.current_sprint())
        self.assertFalse(issue in Issue.objects.archived())
        self.assertFalse(project.has_active_sprint())

        # start sprint
        response = self.client.post(reverse('sprint:startsprint',
                                    kwargs={'project': project.name_short, 'sqn_s': sprint.seqnum}))
        self.assertRedirects(response, reverse('backlog:backlog',
                             kwargs={'project': project.name_short, 'sqn_s': sprint.seqnum}))
        sprint.refresh_from_db()
        project.refresh_from_db()

        # sprint should be current sprint
        self.assertIsNotNone(project.currentsprint)
        self.assertEqual(project.currentsprint.seqnum, sprint.seqnum)
        self.assertTrue(project.has_active_sprint())
        self.assertFalse(sprint in Sprint.objects.get_new_sprints())
        self.assertTrue(sprint in Sprint.objects.get_current_sprints())
        self.assertFalse(sprint in Sprint.objects.get_old_sprints())

        # no issues archived until now
        self.assertFalse(issue in Issue.objects.without_sprint())
        self.assertTrue(issue in Issue.objects.current_sprint())
        self.assertFalse(issue in Issue.objects.archived())
        self.assertFalse(issue2 in Issue.objects.archived())
        self.assertFalse(issue3 in Issue.objects.archived())
        self.assertFalse(issue4 in Issue.objects.archived())

        # set sprint inactive(and archive)
        response = self.client.post(reverse('sprint:stopsprint',
                                            kwargs={'project': project.name_short, 'sqn_s': sprint.seqnum}),
                                    {'sprint': 'new', 'move_to_new_sprint': []},
                                    follow=True)
        self.assertRedirects(response, reverse('backlog:backlog',
                             kwargs={'project': project.name_short}))
        sprint.refresh_from_db()
        project.refresh_from_db()

        # sprint should no more be current sprint. not-done-issues back in backlog (not archived, without sprint)

        self.assertFalse(sprint in Sprint.objects.get_new_sprints())
        self.assertFalse(sprint in Sprint.objects.get_current_sprints())
        self.assertTrue(sprint in Sprint.objects.get_old_sprints())
        self.assertIsNone(project.currentsprint)
        self.assertFalse(project.has_active_sprint())
        self.assertTrue(issue in Issue.objects.without_sprint())
        self.assertFalse(issue in Issue.objects.current_sprint())

        # issue3 is archived because of column type and finished sprint,
        # issue (wrong type), issue2 (wrong type) and 4 (wrong sprint) arent
        self.assertFalse(issue in Issue.objects.archived())
        self.assertFalse(issue2 in Issue.objects.archived())
        self.assertTrue(issue3 in Issue.objects.archived())
        self.assertFalse(issue4 in Issue.objects.archived())

        # issue and issue4 are in same column, both without sprint
        issue4.kanbancol = kanbancol1
        issue4.save()

        # archive column of issue and issue4
        values = {'pos_c': kanbancol1.position}
        response = self.client.post(reverse('issue:archivecol',
                                    kwargs={'project': project.name_short}),
                                    values)
        self.assertRedirects(response, reverse('sprint:sprintboard',
                             kwargs={'project': project.name_short}))
        issue4.refresh_from_db()

        self.assertTrue(issue in Issue.objects.archived())  # archived by archivecol
        self.assertFalse(issue2 in Issue.objects.archived())  # not archived wrong type
        self.assertTrue(issue3 in Issue.objects.archived())  # archived by stopsprint
        self.assertTrue(issue4 in Issue.objects.archived())  # archived by archivecol

    def test_edit_sprint(self):
        self.assertNotEqual(self.sprint.seqnum, -1)

        planned_date = datetime.date.today() + datetime.timedelta(days=10)
        values = {'plandate': planned_date}
        response = self.client.post(reverse('sprint:editsprint',
                                            kwargs={'project': self.project.name_short, 'sqn_s': self.sprint.seqnum}
                                            ), values)
        self.assertRedirects(response, reverse('backlog:backlog',
                             kwargs={'project': self.project.name_short, 'sqn_s': self.sprint.seqnum}))
        response = self.client.get(response['location'])
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Sprint.objects.first().plandate, planned_date)

    def test_add_and_remove_issue_from_sprint(self):
        kanbancol = KanbanColumn(name='Column', position=1, project=self.project)
        kanbancol.save()
        issue = Issue(title="Test-Issue", kanbancol=kanbancol, project=self.project, type="Bug")
        issue.save()

        # add to sprint
        response = self.client.post(reverse('sprint:assigntosprint', kwargs={'project': self.project.name_short}),
                                    {'sqn_i': issue.number}, follow=True,
                                    HTTP_REFERER=reverse('backlog:backlog',
                                                         kwargs={'project': self.project.name_short}))
        self.assertRedirects(response, reverse('backlog:backlog', kwargs={'project': self.project.name_short,
                                                                          'sqn_s': self.sprint.seqnum}))

        self.assertEqual(Issue.objects.get(pk=issue.pk).sprint, Sprint.objects.get(pk=self.sprint.pk))

        # remove from sprint
        response = self.client.post(reverse('sprint:assigntosprint', kwargs={'project': self.project.name_short}),
                                    {'sqn_s': self.sprint.seqnum, 'sqn_i': issue.number}, follow=True,
                                    HTTP_REFERER=reverse('backlog:backlog', kwargs={'project': self.project.name_short})
                                    )
        self.assertRedirects(response, reverse('backlog:backlog', kwargs={'project': self.project.name_short,
                                                                          'sqn_s': self.sprint.seqnum}))

        self.assertEqual(Issue.objects.get(pk=issue.pk).sprint, None)

    def test_dont_assign_issues_to_stoped_sprints(self):
        issue = Issue(title="Test-Issue", project=self.project, type="Bug")
        issue.save()
        issue2 = Issue(title="Test-Issue2", project=self.project, type="Bug")
        issue2.save()

        # start sprint
        self.sprint.set_active()
        self.sprint.save()
        self.project.currentsprint = self.sprint
        self.project.save()
        # assign first issue
        response = self.client.post(reverse('sprint:assigntosprint', kwargs={'project': self.project.name_short}),
                                    {'sqn_i': issue.number}, follow=True,
                                    HTTP_REFERER=reverse('backlog:backlog',
                                                         kwargs={'project': self.project.name_short}))
        self.assertRedirects(response, reverse('backlog:backlog', kwargs={'project': self.project.name_short,
                                                                          'sqn_s': self.sprint.seqnum}))
        # first issue is part of the sprint
        issue.refresh_from_db()
        self.assertIsNotNone(issue.sprint)

        # stop sprint
        response = self.client.post(reverse('sprint:stopsprint',
                                            kwargs={'project': self.project.name_short, 'sqn_s': self.sprint.seqnum}),
                                    {'sprint': 'new', 'move_to_new_sprint': []},
                                    follow=True)
        self.assertEqual(Issue.objects.get(pk=issue.pk).was_in_sprint, True)
        # assign second issue => should fail
        response = self.client.post(reverse('sprint:assigntosprint', kwargs={'project': self.project.name_short}),
                                    {'sqn_i': issue2.number}, follow=True,
                                    HTTP_REFERER=reverse('backlog:backlog',
                                                         kwargs={'project': self.project.name_short}))
        self.assertRedirects(response, reverse('backlog:backlog', kwargs={'project': self.project.name_short}))
        # second issue is NOT part of the sprint
        issue2.refresh_from_db()
        self.assertIsNone(issue2.sprint)

        # create new sprint - so we don't run into the not-sprint part but really into the atomic check for enddate
        sprint2 = Sprint(project=self.project)
        sprint2.save()

        response = self.client.post(reverse('sprint:assigntosprint', kwargs={'project': self.project.name_short}),
                                    {'sqn_i': issue2.number}, follow=True,
                                    HTTP_REFERER=reverse('backlog:backlog', kwargs={'project': self.project.name_short,
                                                                                    'sqn_s': self.sprint.seqnum}))
        self.assertRedirects(response, reverse('backlog:backlog', kwargs={'project': self.project.name_short,
                                                                          'sqn_s': self.sprint.seqnum}))
        issue2.refresh_from_db()
        self.assertIsNone(issue2.sprint)

    def test_stop_sprint_move_issues_to_new_sprint(self):
        # self.sprint should not have started
        self.assertNotEqual(self.sprint.seqnum, -1)
        project = Project(creator=self.user, name_short='APF')
        project.save()
        project.manager.add(self.user)

        sprint = Sprint(project=project)
        sprint.save()
        self.assertEqual(project.sprint.get_new_sprints().count(), 1)

        # columns and issues for testing archiving function
        kanbancol1 = KanbanColumn.objects.get(name='Todo', project=project)
        kanbancol2 = KanbanColumn.objects.get(name='In Progress', project=project)
        kanbancol3 = KanbanColumn.objects.get(name='Done', project=project)

        issue = Issue(title="Test-Issue", kanbancol=kanbancol1, project=project, type="Bug", sprint=sprint)
        issue.save()
        issue2 = Issue(title="Test-Issue2", kanbancol=kanbancol2, project=project, type="Bug", sprint=sprint)
        issue2.save()
        issue3 = Issue(title="Test-Issue3", kanbancol=kanbancol2, project=project, type="Bug", sprint=sprint)
        issue3.save()
        issue4 = Issue(title="Test-Issue4", kanbancol=kanbancol3, project=project, type="Bug")
        issue4.save()
        sprint.set_active()

        # move to autocreated sprint
        response = self.client.post(reverse('sprint:stopsprint',
                                            kwargs={'project': project.name_short, 'sqn_s': sprint.seqnum}),
                                    {'sprint': 'new', 'move_to_new_sprint': [issue.number, issue2.number]},
                                    follow=True)
        # new sprint created
        # self.sprint and sprint created during post request
        self.assertEqual(project.sprint.all().count(), 2)
        self.assertEqual(project.sprint.get_new_sprints().count(), 1)
        self.assertEqual(project.sprint.get_old_sprints().count(), 1)

        # issue, issue2 in new sprint, issue3 in backlog
        self.assertIn(issue, project.sprint.get_new_sprints().last().issue.all())
        self.assertIn(issue2, project.sprint.get_new_sprints().last().issue.all())
        self.assertNotIn(issue3, project.sprint.get_new_sprints().last().issue.all())
        issue3.refresh_from_db()
        self.assertEqual(issue3.sprint, None)

        # move to existing sprint
        sprint = project.sprint.get_new_sprints().last()
        sprint.set_active()
        project.refresh_from_db()
        sprint2 = Sprint(project=project)
        sprint2.save()
        response = self.client.post(reverse('sprint:stopsprint',
                                            kwargs={'project': project.name_short, 'sqn_s': sprint.seqnum}),
                                    {'sprint': sprint2.seqnum, 'move_to_new_sprint': [issue.number]},
                                    follow=True)

        # issue in sprint2, issue2 moved to backlog
        self.assertIn(issue, sprint2.issue.all())
        self.assertNotIn(issue2, sprint2.issue.all())
        issue2.refresh_from_db()
        self.assertEqual(issue2.sprint, None)

    # TODO TESTCASE - move to issue/testcase/test_backlog.py?
    def test_storypoints_in_backlog(self):
        kanbancol = KanbanColumn(name='Column', position=1, project=self.project)
        kanbancol.save()
        issue = Issue(title="Test-Issue", kanbancol=kanbancol, project=self.project, type="Bug", sprint=self.sprint)
        issue.save()
        response = self.client.get(reverse('backlog:backlog',
                                           kwargs={'project': self.project.name_short}
                                           ))
        self.assertNotContains(response, 'Storypoints:')
        issue.storypoints = 5
        issue.save()
        response = self.client.get(reverse('backlog:backlog',
                                           kwargs={'project': self.project.name_short}
                                           ))
        self.assertNotContains(response, 'Storypoints:')
        issue.assignee.add(self.user)
        response = self.client.get(reverse('backlog:backlog',
                                           kwargs={'project': self.project.name_short}
                                           ))
        self.assertContains(response, 'Storypoints:')
        self.assertContains(response, str(self.user.username) + ': 5')
        user2 = get_user_model().objects.create_user('a2', 'b2', 'c2')
        user2.save()
        self.project.developer.add(user2)
        issue.assignee.add(user2)
        response = self.client.get(reverse('backlog:backlog',
                                           kwargs={'project': self.project.name_short}
                                           ))
        self.assertContains(response, str(user2.username) + ': 2.5')
        self.assertContains(response, str(self.user.username) + ': 2.5')
        issue2 = Issue(title="Test-Issue", kanbancol=kanbancol,
                       project=self.project, type="Bug", sprint=self.sprint, storypoints=5)
        issue2.save()
        issue2.assignee.add(self.user)
        response = self.client.get(reverse('backlog:backlog',
                                           kwargs={'project': self.project.name_short}
                                           ))
        self.assertContains(response, str(user2.username) + ': 2.5')
        self.assertContains(response, str(self.user.username) + ': 7.5')

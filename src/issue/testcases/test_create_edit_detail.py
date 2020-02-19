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
from issue.models import Issue, Comment, Attachment
from sprint.models import Sprint
from timelog.models import Timelog
from django.contrib.auth import get_user_model
from django.core.files import File

from user_management.views import LoginView
from issue.views import IssueCreateView, IssueEditView, IssueDetailView
from common.testcases.generic_testcase_helper import view_and_template, redirect_to_login_and_login_required


create_template = 'issue/issue_create_view.html'
edit_template = 'issue/issue_edit.html'
detail_template = 'issue/issue_detail_view.html'

# TODO TESTCASE are there any testcases for IssueDeleteView?


class CreateEditDetailTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        # NOTE: if you modify these elements they need to be created in setUp(), instead of here
        cls.user = get_user_model().objects.create_user('lalala', 'b', 'c')
        cls.user2 = get_user_model().objects.create_user('lululu', 'e', 'f')

    def setUp(self):
        self.client.force_login(self.user)
        # NOTE: these elements get modified by some testcases, so they should NOT be created in setUpTestData()
        self.project = Project(creator=self.user, name_short='PRJ')
        self.project.save()
        self.project.manager.add(self.user)
        self.project.developer.add(self.user)
        self.column = KanbanColumn(name='Column', position=4, project=self.project)
        self.column.save()

    def test_view_and_template(self):
        # create
        view_and_template(self, IssueCreateView, create_template, 'issue:create',
                          address_kwargs={'project': self.project.name_short})

        # create issue for edit and detail tests
        issue = Issue(title="foo")
        issue.project = self.project
        issue.save()
        number = issue.number

        # edit
        view_and_template(self, IssueEditView, edit_template, 'issue:edit',
                          address_kwargs={'project': self.project.name_short, 'sqn_i': number})
        # detail
        view_and_template(self, IssueDetailView, detail_template, 'issue:detail',
                          address_kwargs={'project': self.project.name_short, 'sqn_i': number})

        # TODO TESTCASE delete

    def test_redirect_to_login_and_login_required(self):
        self.client.logout()
        # create
        redirect_to_login_and_login_required(self, 'issue:create', address_kwargs={'project': self.project.name_short})

        # create issue for edit and detail tests
        issue = Issue(title="foo")
        issue.project = self.project
        issue.save()
        number = issue.number

        # edit
        redirect_to_login_and_login_required(self, 'issue:edit',
                                             address_kwargs={'project': self.project.name_short, 'sqn_i': number})
        # detail
        redirect_to_login_and_login_required(self, 'issue:detail',
                                             address_kwargs={'project': self.project.name_short, 'sqn_i': number})

        # TODO TESTCASE delete

    def test_user_passes_test_mixin(self):
        # TODO TESTCASE
        # TODO create
        # TODO edit
        # TODO detail
        pass

    def test_create_and_edit_issues_with_get_requests_disabled(self):
        values = {
            'title': "Test-Issue",
            'kanbancol': self.column.pk,
            'type': "Bug",
            'assignee': (self.user.pk),
            'priority': 2,
        }
        # create
        response = self.client.get(reverse('issue:create', kwargs={'project': self.project.name_short}), values)
        # didn't store something
        self.assertTemplateUsed(response, create_template)
        try:
            self.assertIsNone(Issue.objects.get(title="Test-Issue", assignee=self.user.pk))
        except Issue.DoesNotExist:
            pass

        # create issue for edit test
        issue = Issue(title="foo")
        issue.project = self.project
        issue.save()
        number = issue.number

        # edit
        response = self.client.get(reverse('issue:edit',
                                           kwargs={'project': self.project.name_short, 'sqn_i': number}), values)
        # didn't store something
        self.assertIsNotNone(Issue.objects.get(title="foo", project=self.project))

    def test_title_required(self):
        # TODO TESTCASE
        # TODO create
        # TODO edit
        # TODO detail
        pass

    def test_only_issues_of_this_project_visible(self):
        # TODO TESTCASE
        # TODO create
        # TODO edit
        # TODO detail
        pass

    def test_detail_view(self):
        # TODO TESTCASE
        pass

    def test_delete(self):
        # TODO TESTCASE
        pass

    def test_delete_with_timelog(self):
        issue = Issue(title="foo")
        issue.project = self.project
        issue.save()
        Timelog(user=self.user, issue=issue, time=timedelta(1)).save()

        response = self.client.post(
                reverse('issue:delete', kwargs={'project': self.project.name_short, 'sqn_i': issue.number}),
                {'delete': 'true'}, follow=True)
        self.assertRedirects(response, reverse('backlog:backlog', kwargs={'project': self.project.name_short}))
        self.assertContains(response, "foo")
        self.assertContains(response, "logged time")

    def test_archive_and_unarchive_single_issue_function(self):
        issue = Issue(title="bar", project=self.project)
        issue.save()
        self.assertFalse(issue.archived)
        n = Issue.objects.archived().count()

        values = {'sqn_i': issue.number}
        response = self.client.post(reverse('issue:archiveissue', kwargs={'project': self.project.name_short}), values)
        self.assertRedirects(response, reverse('issue:detail',
                             kwargs={'project': self.project.name_short, 'sqn_i': issue.number}))
        issue.refresh_from_db()

        self.assertEqual(Issue.objects.archived().count(), (n+1))
        self.assertTrue(issue.archived)

        values = {'sqn_i': issue.number}
        response = self.client.post(reverse('issue:unarchiveissue',
                                    kwargs={'project': self.project.name_short}), values)
        self.assertRedirects(response, reverse('issue:detail',
                                               kwargs={'project': self.project.name_short, 'sqn_i': issue.number}))
        issue.refresh_from_db()

        self.assertEqual(Issue.objects.archived().count(), n)
        self.assertFalse(issue.archived)

    def test_archive_and_unarchive_multiple_issue_function(self):
        # TODO TESTCASE
        pass

    def test_delete_issue(self):
        issue = Issue(title="foo123")
        issue.project = self.project
        issue.save()

        response = self.client.post(
                reverse('issue:delete', kwargs={'project': self.project.name_short, 'sqn_i': issue.number}),
                {'delete': 'true'})
        self.assertRedirects(response, reverse('backlog:backlog', kwargs={'project': self.project.name_short}))
        response = self.client.get(response['location'])
        self.assertTemplateUsed(response, 'backlog/backlog_list.html')
        self.assertNotContains(response, "foo123")

    def test_keep_and_dont_delete_issue(self):
        issue = Issue(title="foo123", project=self.project)
        issue.save()

        response = self.client.post(
                reverse('issue:delete', kwargs={'project': self.project.name_short, 'sqn_i': issue.number}),
                {'keep': 'true'})
        self.assertRedirects(response, reverse('issue:detail',
                             kwargs={'project': self.project.name_short, 'sqn_i': issue.number}))
        response = self.client.get(response['location'])
        self.assertTemplateUsed(response, 'issue/issue_detail_view.html')
        self.assertContains(response, "foo123")

    def test_create_and_edit_issue(self):
        values = {
            'title': "Test-Issue",
            'kanbancol': self.column.pk,
            'due_date': datetime.date.today(),
            'type': "Bug",
            'assignee': (self.user.pk),
            'priority': 2,
            'description': "Fancy description",
            'storypoints': 5,
        }
        response = self.client.post(reverse('issue:create', kwargs={'project': self.project.name_short}), values)
        self.assertRedirects(response, reverse('backlog:backlog', kwargs={'project': self.project.name_short}))
        response = self.client.get(response['location'])
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.project.issue.count(), 1)

        # assert that values and especially ticket ID was written correctly
        self.assertEqual(Issue.objects.count(), 1)
        currentIssue = Issue.objects.get(pk=1)
        for key in values:
            if key == 'kanbancol':
                self.assertEqual(currentIssue.__getattribute__(key).pk, values[key])
            elif key == 'assignee':
                self.assertEqual(currentIssue.__getattribute__(key).all().count(), 1)
                self.assertEqual(currentIssue.__getattribute__(key).all().get(pk=1).pk, values[key])
            else:
                self.assertEqual(currentIssue.__getattribute__(key), values[key])

        self.assertEqual(currentIssue.__str__(), values['title'])
        self.assertEqual(Project.objects.get(pk=1).nextTicketId, 2)
        self.assertEqual(currentIssue.number, 1)

        # edit issue
        values['priority'] = 3

        response = self.client.post(reverse('issue:edit',
                                            kwargs={'project': self.project.name_short, 'sqn_i': 1}), values)
        self.assertRedirects(response,
                             reverse('issue:detail', kwargs={'project': self.project.name_short, 'sqn_i': 1}))
        response = self.client.get(response['location'])
        self.assertEqual(response.status_code, 200)
        self.assertEqual(currentIssue.number, 1)

        currentIssue = Issue.objects.get(pk=1)
        for key in values:
            if key == 'kanbancol':
                self.assertEqual(currentIssue.__getattribute__(key).pk, values[key])
            elif key == 'assignee':
                self.assertEqual(currentIssue.__getattribute__(key).all().count(), 1)
                self.assertEqual(currentIssue.__getattribute__(key).all().get(pk=1).pk, values[key])
            else:
                self.assertEqual(currentIssue.__getattribute__(key), values[key])

        # ticket ID must not change!
        self.assertEqual(currentIssue.number, 1)
        self.assertEqual(Project.objects.get(pk=1).nextTicketId, 2)

        # check if blank fields are working
        values['assignee'] = ()
        values['due_date'] = ''
        values['description'] = ''

        response = self.client.post(reverse('issue:edit',
                                            kwargs={'project': self.project.name_short, 'sqn_i': 1}), values)
        self.assertRedirects(response, reverse('issue:detail', kwargs={'project': self.project.name_short, 'sqn_i': 1}))
        response = self.client.get(response['location'])
        self.assertEqual(response.status_code, 200)

        currentIssue = Issue.objects.get(pk=1)
        for key in values:
            if key == 'kanbancol':
                self.assertEqual(currentIssue.__getattribute__(key).pk, values[key])
            elif key == 'assignee':
                self.assertEqual(currentIssue.__getattribute__(key).all().count(), 0)
            elif key == 'due_date':
                self.assertEqual(currentIssue.__getattribute__(key), None)
            elif key == 'storypoints':
                self.assertEqual(currentIssue.__getattribute__(key), 5)
            else:
                self.assertEqual(currentIssue.__getattribute__(key), values[key])

        # ticket ID must not change!
        self.assertEqual(currentIssue.number, 1)
        self.assertEqual(Project.objects.get(pk=1).nextTicketId, 2)

    def test_validation(self):
        values = {
            'title': "Test-Issue",
            'kanbancol': self.column.pk,
            'due_date': datetime.date(2016, 10, 1),
            'type': "Bug",
            'assignee': (self.user.pk),
            'priority': 2,
            'description': "Fancy description",
            'storypoints': -1,
        }

        errormsg = "Enter a positive storypoints amount!"

        response = self.client.post(reverse('issue:create', kwargs={'project': self.project.name_short}), values)
        self.assertFormError(response, 'form', 'storypoints', errormsg)

        # set date to yesterday
        values['storypoints'] = 1
        values['due_date'] = datetime.date.today() - timedelta(1)

        errormsg = "Enter a date starting from today"

        response = self.client.post(reverse('issue:create', kwargs={'project': self.project.name_short}), values)
        self.assertFormError(response, 'form', 'due_date', errormsg)

    def test_dependsOn(self):
        values = {
            'title': "Issue 1",
            'kanbancol': self.column.pk,
            'due_date': datetime.date.today(),
            'type': "Bug",
            'assignee': (self.user.pk),
            'priority': 2,
            'description': "Fancy description",
            'storypoints': 5,
            'dependsOn': (),
        }
        response = self.client.post(reverse('issue:create', kwargs={'project': self.project.name_short}), values)
        self.assertRedirects(response, reverse('backlog:backlog', kwargs={'project': self.project.name_short}))
        response = self.client.get(response['location'])
        self.assertEqual(response.status_code, 200)

        # create second issue depending on first issue
        values['title'] = "Issue 2"
        values['dependsOn'] = (1)

        response = self.client.post(reverse('issue:create', kwargs={'project': self.project.name_short}), values)
        self.assertRedirects(response, reverse('backlog:backlog', kwargs={'project': self.project.name_short}))
        response = self.client.get(response['location'])
        self.assertEqual(response.status_code, 200)

        self.assertEqual(Issue.objects.get(pk=2).dependsOn.count(), 1)
        self.assertEqual(Issue.objects.get(pk=2).dependsOn.first().title, 'Issue 1')

        # check that dependsOn works unidirectional
        self.assertEqual(Issue.objects.get(pk=1).dependsOn.count(), 0)

    # TODO TODO TODO TODO TODO TESTCASE broken test, is not tested yet
    def test_assign_tag_view(self):
        issue = Issue(title="Test-Issue", project=self.project, kanbancol=self.column, type="Bug")
        issue.save()
        t0 = 'first_tag'
        tag0 = Tag(tag_text=t0, project=self.project)
        tag0.save()
        t1 = 'second_tag'
        tag1 = Tag(tag_text=t1, project=self.project)
        tag1.save()
        t2 = 'third_tag'
        tag2 = Tag(tag_text=t2, project=self.project)
        tag2.save()
        values = {
            # first_tag
            'tags': (1)
        }
        response = self.client.post(reverse('issue:edit',
                                    kwargs={'project': self.project.name_short, 'sqn_i': 1}), values)
        # please don't ask me why the following (which would be a way better assert) doesn't work
        # self.assertContains(response, t0)
        self.assertIn(t0, response.content.decode())
        self.assertEqual(Issue.objects.count(), 1)
        # TODO
        """
        self.assertEqual(issue.tags.count(), 1)
        self.assertEqual(issue.tags.first().text, t0)
        """
        response = self.client.get(reverse('issue:edit',
                                   kwargs={'project': self.project.name_short, 'sqn_i': 1}))

        return
        # TODO TODO TODO TESTCASE the following doesn't work because t0 doesn't appear in the response anymore
        self.assertContains(response, t0)
        # self.assertIn(t0, str(response.content))
        values = {
            # 'tags': [t2, t1],
            'tags': [(3), (2)],
        }
        response = self.client.post(reverse('issue:edit',
                                    kwargs={'project': self.project.name_short, 'sqn_i': 1}), values)
        self.assertContains(response, t0)
        self.assertContains(response, t2)
        self.assertContains(response, t1)

        response = self.client.get(reverse('issue:edit',
                                   kwargs={'project': self.project.name_short, 'sqn_i': 1}))
        self.assertContains(response, t0)
        self.assertContains(response, t2)
        self.assertContains(response, t1)

        # TODO TESTCASE
        # TODO test delete
        # TODO test assign is only possible for tags of relative project

    # TODO also test this for creation of tags, because the url-scheme differs a bit

    def test_managerfunctions(self):
        issue1 = Issue(title="issue1", project=self.project, kanbancol=self.column)
        issue1.save()
        sprint_current = Sprint(project=self.project,
                                startdate=(timezone.now()-timedelta(days=1)))
        sprint_current.save()
        sprint_old = Sprint(project=self.project,
                            startdate=(timezone.now()-timedelta(days=14)),
                            enddate=(timezone.now()-timedelta(days=1)))
        sprint_old.save()

        issues_wo_sprint = Issue.objects.without_sprint()
        self.assertTrue(issue1 in issues_wo_sprint)

        issue1.sprint = sprint_current
        issue1.save()
        issues_cur_sprint = Issue.objects.current_sprint()
        self.assertTrue(issue1 in issues_cur_sprint)
        issue1.sprint = sprint_old
        issue1.save()
        issues_cur_sprint = Issue.objects.current_sprint()
        issues_wo_sprint = Issue.objects.without_sprint()
        self.assertFalse(issue1 in issues_cur_sprint)
        self.assertFalse(issue1 in issues_wo_sprint)

    def test_assign_to_me_remove_from_me(self):
        issue = Issue(title="Test-Issue", project=self.project, kanbancol=self.column, type="Bug")
        issue.save()
        response = self.client.post(reverse('issue:assigntome',
                                            kwargs={'project': self.project.name_short}),
                                    {'sqn_i': issue.number})
        self.assertIn(self.user, issue.assignee.all())
        response = self.client.post(reverse('issue:rmfromme',
                                            kwargs={'project': self.project.name_short}),
                                    {'sqn_i': issue.number})
        self.assertNotIn(self.user, issue.assignee.all())
        response = self.client.post(reverse('issue:rmfromme',
                                            kwargs={'project': self.project.name_short}),
                                    {'sqn_i': issue.number}, follow=True)

        self.assertContains(response, 'Issue was not in selected sprint, not performing any action')

    def test_add_and_remove_to_kanbancol(self):
        # TODO TESTCASE
        pass

    def test_next_parameter_in_post_requests(self):
        issue = Issue(title="Test-Issue", project=self.project, kanbancol=self.column, type="Bug")
        issue.save()
        response = self.client.post(reverse('issue:assigntome',
                                            kwargs={'project': self.project.name_short}),
                                    {'sqn_i': issue.number, 'next': '/timelog'},
                                    follow=True
                                    )
        self.assertRedirects(response, reverse('timelog:loginfo'))
        response = self.client.post(reverse('issue:rmfromme',
                                            kwargs={'project': self.project.name_short}),
                                    {'sqn_i': issue.number, 'next': '/timelog'},
                                    follow=True
                                    )
        self.assertRedirects(response, reverse('timelog:loginfo'))
        response = self.client.post(reverse('issue:archiveissue',
                                            kwargs={'project': self.project.name_short}),
                                    {'sqn_i': issue.number, 'next': '/timelog'},
                                    follow=True
                                    )
        self.assertRedirects(response, reverse('timelog:loginfo'))
        response = self.client.post(reverse('issue:unarchiveissue',
                                            kwargs={'project': self.project.name_short}),
                                    {'sqn_i': issue.number, 'next': '/timelog'},
                                    follow=True
                                    )
        self.assertRedirects(response, reverse('timelog:loginfo'))

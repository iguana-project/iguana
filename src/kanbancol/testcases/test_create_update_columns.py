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
from django.utils import translation
from django.contrib.auth import get_user_model

from kanbancol.models import KanbanColumn
from kanbancol.views import KanbanColumnCreateView, KanbanColumnBreadcrumbView, KanbanColumnUpdateView,\
                            KanbanColumnUpView, KanbanColumnDownView, KanbanColumnDeleteView
from project.models import Project
from issue.models import Issue
from common.testcases.generic_testcase_helper import view_and_template, redirect_to_login_and_login_required


class ColumnTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        # NOTE: if you modify these elements they need to be created in setUp(), instead of here
        cls.user = get_user_model().objects.create_user('test', 'test@testing.com', 'test1234')

    def setUp(self):
        # NOTE: these elements get modified by some testcases, so they should NOT be created in setUpTestData()
        translation.activate('en')
        self.client.force_login(self.user)
        self.project = Project(creator=self.user, name_short='test', name='Testproject', description='asdf')
        self.project.save()
        self.project.manager.add(self.user)
        self.column = KanbanColumn(name='Column', project=self.project)
        self.column.save()

    def test_view_and_template(self):
        # create
        view_and_template(self, KanbanColumnCreateView, 'kanbancol/create_kanbancolumn.html', 'kanbancol:create',
                          address_kwargs={'project': self.project.name_short})
        # breadcrumb
        # TODO TESTCASE what is the correct reverse call for the breadcrumb?
        # view_and_template(self, KanbanColumnBreadcrumbView, 'kanbancol/breadcrumbs.html', 'kanbancol',
        #                   address_kwargs={'project': self.project.name_short, 'position': 0})

        # update
        view_and_template(self, KanbanColumnUpdateView, 'kanbancol/update_kanbancolumn.html', 'kanbancol:update',
                          address_kwargs={'project': self.project.name_short, 'position': 3})

        # moveup
        # TODO TESTCASE what is wrong with this address_kwargs?
        # view_and_template(self, KanbanColumnUpView, 'project/project_edit.html', 'kanbancol:moveup',
        #                   address_kwargs={'project': self.project.name_short, 'position': 2})

        # movedown
        # TODO TESTCASE what is wrong with this address_kwargs?
        # view_and_template(self, KanbanColumnDownView, 'project/project_edit.html', 'kanbancol:movedown',
        #                   address_kwargs={'project': self.project.name_short, 'position': 2})

        # delete
        view_and_template(self, KanbanColumnDeleteView, 'confirm_delete.html', 'kanbancol:delete',
                          address_kwargs={'project': self.project.name_short, 'position': 3})

    def test_redirect_to_login_and_login_required(self):
        self.client.logout()
        # TODO TESTCASE see invite_users
        #      redirect_to_login_and_login_required()
        # TODO which views?
        #      - create
        #      - update
        #      - delete
        #      - moveup
        #      - movedown
        #      - breadcrumb
        #      - ...
        pass

    def test_user_passes_test_mixin(self):
        # TODO TESTCASE
        pass

    def test_create_and_edit_kanban_with_get_request_disabled(self):
        # TODO TESTCASE
        pass

    def test_issues_from_other_projects_invisible(self):
        # TODO TESTCASE
        pass

    def test_default_columns(self):
        # create
        response = self.client.get(reverse('project:edit', kwargs={'project': self.project.name_short}))
        self.assertContains(response, 'Todo', count=1)
        self.assertContains(response, 'In Progress', count=1)
        self.assertContains(response, 'Done', count=1)

        # delete
        response = self.client.post(reverse('project:delete', kwargs={'project': self.project.name_short}),
                                    {'delete': 'true'})
        self.assertEqual(KanbanColumn.objects.count(), 0)

    def test_create_column(self):
        # TODO TESTCASE
        pass

    def test_update_column(self):
        # TODO TESTCASE
        pass

    def test_delete_column(self):
        # TODO TESTCASE
        pass

    def test_delete_column_rejected_cuz_issues_assigned(self):
        # TODO TESTCASE
        pass

    def test_issue_kanban_moveleftright(self):
        self.assertEqual(self.project.kanbancol.count(), 4)
        issue1 = Issue(title="issue1", project=self.project, kanbancol=self.project.kanbancol.first())
        issue1.save()

        self.assertEqual(issue1.get_left_kCol_for_issue(), -1)
        self.assertEqual(issue1.get_right_kCol_for_issue(), 1)

        # move issue to next row and check results
        issue1.kanbancol = self.project.kanbancol.get(position='1')
        issue1.save()
        self.assertEqual(issue1.get_left_kCol_for_issue(), 0)
        self.assertEqual(issue1.get_right_kCol_for_issue(), 2)

        # move issue to last row and check results
        issue1.kanbancol = self.project.kanbancol.get(position='3')
        issue1.save()
        self.assertEqual(issue1.get_left_kCol_for_issue(), 2)
        self.assertEqual(issue1.get_right_kCol_for_issue(), -1)

        # test view function
        response = self.client.post(reverse('issue:setkanbancol', kwargs={'project': self.project.name_short}),
                                    {'sqn_k': '0',
                                     'sqn_i': issue1.number,
                                     }, follow=True)
        self.assertRedirects(response, reverse('sprint:sprintboard', kwargs={'project': self.project.name_short}))
        issue1.refresh_from_db()
        self.assertEqual(issue1.kanbancol.position, 0)

        # check if error handling works (set col too high)
        response = self.client.post(reverse('issue:setkanbancol', kwargs={'project': self.project.name_short}),
                                    {'sqn_k': '4',
                                     'sqn_i': issue1.number,
                                     }, follow=True)
        self.assertRedirects(response, reverse('sprint:sprintboard', kwargs={'project': self.project.name_short}))
        self.assertEqual(len(list(response.context['messages'])), 1)
        issue1.refresh_from_db()
        self.assertEqual(issue1.kanbancol.position, 0)

        # check with invalid issue
        response = self.client.post(reverse('issue:setkanbancol', kwargs={'project': self.project.name_short}),
                                    {'sqn_k': '2',
                                     'sqn_i': issue1.number+1,
                                     }, follow=True)
        self.assertRedirects(response, reverse('sprint:sprintboard', kwargs={'project': self.project.name_short}))
        self.assertEqual(len(list(response.context['messages'])), 1)
        issue1.refresh_from_db()
        self.assertEqual(issue1.kanbancol.position, 0)

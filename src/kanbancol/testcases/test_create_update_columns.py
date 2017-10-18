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
from project.models import Project
from issue.models import Issue


class ColumnTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        # NOTE: if you modify this element it needs to be created in setUp, instead of here
        cls.user = get_user_model().objects.create_user('test', 'test@testing.com', 'test1234')

    def setUp(self):
        translation.activate('en')
        self.client.force_login(self.user)
        self.project = Project(creator=self.user, name_short='test', name='Testproject', description='asdf')
        self.project.save()
        self.project.manager.add(self.user)
        self.column = KanbanColumn(name='Column', project=self.project)
        self.column.save()

    def test_view_and_template(self):
        # TODO TESTCASE see invite_users/testcases/test_invite_users.py as example
        pass

    def test_redirect_to_login_and_login_required(self):
        # TODO TESTCASE see invite_users/testcases/test_invite_users.py as example
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
        self.assertRedirects(response, reverse('issue:projList', kwargs={'project': self.project.name_short}))
        issue1.refresh_from_db()
        self.assertEqual(issue1.kanbancol.position, 0)

        # check if error handling works (set col too high)
        response = self.client.post(reverse('issue:setkanbancol', kwargs={'project': self.project.name_short}),
                                    {'sqn_k': '4',
                                     'sqn_i': issue1.number,
                                     }, follow=True)
        self.assertRedirects(response, reverse('issue:projList', kwargs={'project': self.project.name_short}))
        self.assertEqual(len(list(response.context['messages'])), 1)
        issue1.refresh_from_db()
        self.assertEqual(issue1.kanbancol.position, 0)

        # check with invalid issue
        response = self.client.post(reverse('issue:setkanbancol', kwargs={'project': self.project.name_short}),
                                    {'sqn_k': '2',
                                     'sqn_i': issue1.number+1,
                                     }, follow=True)
        self.assertRedirects(response, reverse('issue:projList', kwargs={'project': self.project.name_short}))
        self.assertEqual(len(list(response.context['messages'])), 1)
        issue1.refresh_from_db()
        self.assertEqual(issue1.kanbancol.position, 0)

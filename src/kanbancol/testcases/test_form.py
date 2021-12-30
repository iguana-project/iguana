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
from collections import deque

from common.testcases.generic_testcase_helper import user_doesnt_pass_test_and_gets_404
from issue.models import Issue
from kanbancol.models import KanbanColumn
from project.models import Project
from django.contrib.auth import get_user_model


class FormTest(TestCase):
    short = 'proj'

    @classmethod
    def setUpTestData(cls):
        # NOTE: if you modify these elements they need to be created in setUp(), instead of here
        cls.user = get_user_model().objects.create_user('a', 'b', 'c')
        cls.user2 = get_user_model().objects.create_user('d', 'e', 'f')
        cls.project = Project(creator=cls.user, name_short=cls.short)

        cls.project.save()
        cls.project.manager.set((cls.user.pk,))
        cls.project.developer.add(cls.user2)
        cls.project.save()

    def setUp(self):
        self.client.force_login(self.user)
        # NOTE: these elements get modified by some testcases, so they should NOT be created in setUpTestData()

    def test_permission_functions(self):
        col = self.project.kanbancol.first()

        self.assertEqual(col.user_has_read_permissions(self.user), True)
        self.assertEqual(col.user_has_write_permissions(self.user), True)

        self.assertEqual(col.user_has_read_permissions(self.user2), True)
        self.assertEqual(col.user_has_write_permissions(self.user2), False)

    # TODO
    def test_views_access_denied(self):
        self.client.force_login(self.user2)

        vals = {
            'name': "Testcolumn",
            'type': 'ToDo',
            'project': self.project.pk
        }

        numCols = KanbanColumn.objects.count()

        user_doesnt_pass_test_and_gets_404(self, 'kanbancol:create', address_kwargs={'project': self.short},
                                           get_kwargs=vals)

        self.assertEqual(numCols, KanbanColumn.objects.count())

        vals = {
            'name': "Testmodification",
            'type': 'ToDo',
        }
        user_doesnt_pass_test_and_gets_404(self, 'kanbancol:update',
                                           address_kwargs={'position': 3, 'project': self.short},
                                           get_kwargs=vals)

        user_doesnt_pass_test_and_gets_404(self, 'kanbancol:delete',
                                           address_kwargs={'position': 3, 'project': self.short},
                                           get_kwargs={'delete': 'true'})

        user_doesnt_pass_test_and_gets_404(self, 'kanbancol:movedown',
                                           address_kwargs={'project': self.short, 'position': 1})

        user_doesnt_pass_test_and_gets_404(self, 'kanbancol:moveup',
                                           address_kwargs={'project': self.short, 'position': 1})

        self.client.force_login(self.user)

    # TODO
    def test_up_down_view_get_404(self):
        response = self.client.get(reverse('kanbancol:movedown', kwargs={'project': self.short, 'position': 1}),
                                   follow=True)
        self.assertEqual(response.status_code, 404)

        response = self.client.get(reverse('kanbancol:moveup', kwargs={'project': self.short, 'position': 1}),
                                   follow=True)
        self.assertEqual(response.status_code, 404)

    # TODO TESTCASE split into smaller, independent tests
    # TODO
    def test_form(self):
        # create
        vals = {
            'name': "Testcolumn",
            'type': 'ToDo',
            'project': self.project.pk
        }
        response = self.client.post(reverse('kanbancol:create', kwargs={'project': self.short}), vals)
        self.client.get(reverse("project:edit", kwargs={"project": self.short}))
        self.assertRedirects(response, reverse('project:edit', kwargs={'project': self.short}))

        response = self.client.get(response['location'])
        self.assertEqual(response.status_code, 200)
        # We always insert at the end
        self.assertEqual(response.context['columns'][3].name, "Testcolumn")
        self.assertEqual(str(response.context['columns'][3]), "Testcolumn")

        # modify
        vals = {
            'name': "Testmodification",
            'type': 'ToDo',
        }
        response = self.client.post(reverse('kanbancol:update', kwargs={'position': 3, 'project': self.short}), vals)
        self.assertRedirects(response, reverse('project:edit', kwargs={'project': self.short}))

        response = self.client.get(response['location'])
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['columns'][3].name, "Testmodification")

        # assign issue to column and try to delete
        issue = Issue(
            title="Test-Issue",
            kanbancol=KanbanColumn.objects.get(position=3, project__name_short=self.short),
            project=self.project, type="Bug"
        )
        issue.save()

        self.assertEqual(KanbanColumn.objects.count(), 4)

        response = self.client.post(reverse('kanbancol:delete', kwargs={'position': 3, 'project': self.short}),
                                    {'delete': 'true'})
        self.assertRedirects(response, reverse('project:edit', kwargs={'project': self.short}))
        self.assertEqual(KanbanColumn.objects.count(), 4)

        issue.kanbancol = KanbanColumn.objects.get(position=2, project__name_short=self.short)
        issue.save()

        # delete
        response = self.client.post(reverse('kanbancol:delete', kwargs={'position': 3, 'project': self.short}),
                                    {'delete': 'true'})
        self.assertRedirects(response, reverse('project:edit', kwargs={'project': self.short}))
        response = self.client.get(response['location'])
        self.assertEqual(KanbanColumn.objects.count(), 3)
        self.assertNotContains(response, vals["name"])

    # TODO
    def test_movement(self):
        cols = [
            KanbanColumn.objects.get(name="Todo").name,
            KanbanColumn.objects.get(name="In Progress").name,
            KanbanColumn.objects.get(name="Done").name,
        ]

        # move Todo down (last move no effect)
        for i in range(3):
            todo = cols[i]
            del cols[i]
            cols.insert(i+1, todo)
            response = self.client.post(reverse('kanbancol:movedown', kwargs={'project': self.short, 'position': i}))
            self.assertRedirects(response, reverse('project:edit', kwargs={'project': self.short}))
            for i, name in enumerate(cols):
                self.assertEqual(i, KanbanColumn.objects.get(name=name).position, name)

        # and the same back up
        for i in range(2, -1, -1):
            todo = cols[i]
            del cols[i]
            cols.insert(max(i-1, 0), todo)
            response = self.client.post(reverse('kanbancol:moveup', kwargs={'project': self.short, 'position': i}))
            self.assertRedirects(response, reverse('project:edit', kwargs={'project': self.short}))
            for i, name in enumerate(cols):
                self.assertEqual(i, KanbanColumn.objects.get(name=name).position, name)

    def test_position_of_default_cols(self):
        self.assertEqual("Todo", KanbanColumn.objects.get(position=0).name)
        self.assertEqual("In Progress", KanbanColumn.objects.get(position=1).name)
        self.assertEqual("Done", KanbanColumn.objects.get(position=2).name)

    # Explicitly tests for the position instead of relying on "order" \mapsto "position"
    # also tests whether the original ToDo and Done columns can be deleted
    def test_movement_caused_by_create_and_delete_and_remove_original_todo_and_done_cols(self):
        todo_name = "Todo"
        in_progress_name = "In Progress"
        done_name = "Done"
        cols = deque([todo_name, in_progress_name, done_name])

        # default cols
        for i in range(len(cols)):
            self.assertEqual(i, KanbanColumn.objects.get(name=cols[i]).position, cols[i])

        # creation always appends at the end
        new_col_name = "So effing done"
        cols.append(new_col_name)
        self.client.post(reverse('kanbancol:create', kwargs={'project': self.short}),
                         {'name': new_col_name, 'type': 'Done'})
        for i in range(len(cols)):
            self.assertEqual(i, KanbanColumn.objects.get(name=cols[i]).position, cols[i])

        # create new ToDo column, so we can delete the original one
        new_col_name = "ToDo2"
        cols.append(new_col_name)
        cols.remove(todo_name)
        self.client.post(reverse('kanbancol:create', kwargs={'project': self.short}),
                         {'name': new_col_name, 'type': 'ToDo'})
        self.client.post(reverse('kanbancol:delete', kwargs={'project': self.short, 'position': 0}), {'delete': 'true'})
        for i in range(len(cols)):
            self.assertEqual(i, KanbanColumn.objects.get(name=cols[i]).position, cols[i])

        # create new Done column, so we can delete the original one
        new_col_name = "Done2"
        cols.append(new_col_name)
        cols.remove(done_name)
        self.client.post(reverse('kanbancol:create', kwargs={'project': self.short}),
                         {'name': new_col_name, 'type': 'Done'})
        self.client.post(reverse('kanbancol:delete', kwargs={'project': self.short, 'position': 1}), {'delete': 'true'})
        for i in range(len(cols)):
            self.assertEqual(i, KanbanColumn.objects.get(name=cols[i]).position, cols[i])

    def test_there_has_to_be_at_least_one_todo_and_one_done_column(self):
        vals = {
            'name': "Testmodification",
            'type': 'InProgress',
        }
        current_columns = list(KanbanColumn.objects.filter(project__name_short=self.short))
        self.assertEqual(3, len(current_columns))

        response = self.client.post(reverse('kanbancol:update',
                                            kwargs={'position': 0, 'project': self.project.name_short}),
                                    vals)
        # no changes; there has to be at least one column of type ToDo
        self.assertContains(response, 'edit rejected')
        self.assertEquals(current_columns, list(KanbanColumn.objects.filter(project__name_short=self.short)))

        response = self.client.post(reverse('kanbancol:update',
                                            kwargs={'position': 2, 'project': self.project.name_short}),
                                    vals)
        # no changes; there has to be at least one column of type Done
        self.assertContains(response, 'edit rejected')
        self.assertEquals(current_columns, list(KanbanColumn.objects.filter(project__name_short=self.short)))

        response = self.client.post(reverse('kanbancol:delete',
                                            kwargs={'position': 0, 'project': self.project.name_short}),
                                    {'delete': 'true'},
                                    follow=True)
        # no changes; there has to be at least one column of type ToDo
        self.assertContains(response, 'delete was rejected')
        self.assertEquals(current_columns, list(KanbanColumn.objects.filter(project__name_short=self.short)))

        response = self.client.post(reverse('kanbancol:delete',
                                            kwargs={'position': 2, 'project': self.project.name_short}),
                                    {'delete': 'true'},
                                    follow=True)
        # no changes; there has to be at least one column of type Done
        self.assertContains(response, 'delete was rejected')
        self.assertEquals(current_columns, list(KanbanColumn.objects.filter(project__name_short=self.short)))

        # it is possible to delete all columns of type "InProgress"
        response = self.client.post(reverse('kanbancol:delete',
                                            kwargs={'position': 1, 'project': self.project.name_short}),
                                    {'delete': 'true'},
                                    follow=True)
        self.assertNotContains(response, 'delete was rejected')
        del(current_columns[1])
        self.assertEquals(current_columns, list(KanbanColumn.objects.filter(project__name_short=self.short)))

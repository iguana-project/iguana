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

    def test_up_down_view_get_404(self):
        response = self.client.get(reverse('kanbancol:movedown', kwargs={'project': self.short, 'position': 1}),
                                   follow=True)
        self.assertEqual(response.status_code, 404)

        response = self.client.get(reverse('kanbancol:moveup', kwargs={'project': self.short, 'position': 1}),
                                   follow=True)
        self.assertEqual(response.status_code, 404)

    # TODO TESTCASE split into smaller, independent tests
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
                self.assertEqual(i, KanbanColumn.objects.get(name=name).position)

        # and the same back up
        for i in range(2, -1, -1):
            todo = cols[i]
            del cols[i]
            cols.insert(max(i-1, 0), todo)
            response = self.client.post(reverse('kanbancol:moveup', kwargs={'project': self.short, 'position': i}))
            self.assertRedirects(response, reverse('project:edit', kwargs={'project': self.short}))
            for i, name in enumerate(cols):
                self.assertEqual(i, KanbanColumn.objects.get(name=name).position)

    def test_movement_caused_by_create_and_delete(self):
        todo = KanbanColumn.objects.get(name="Todo")
        in_progress = KanbanColumn.objects.get(name="In Progress")
        done = KanbanColumn.objects.get(name="Done")
        cols = deque([todo.name, in_progress.name, done.name])

        # default cols
        for i in range(len(cols)):
            self.assertEqual(i, KanbanColumn.objects.get(name=cols[i]).position)

        # creation always appends at the end
        name = "So effing done"
        cols.append(name)
        self.client.post(reverse('kanbancol:create', kwargs={'project': self.short}), {'name': name, 'type': 'Done'})
        for i in range(len(cols)):
            self.assertEqual(i, KanbanColumn.objects.get(name=cols[i]).position)

        # delete todo-col
        cols.remove(todo.name)
        # create new ToDo column, so we can delete the other one
        self.client.post(reverse('kanbancol:create', kwargs={'project': self.short}), {'name': 'ToDo2', 'type': 'ToDo'})
        self.client.post(reverse('kanbancol:delete', kwargs={'project': self.short, 'position': 0}), {'delete': 'true'})
        for i in range(len(cols)):
            self.assertEqual(i, KanbanColumn.objects.get(name=cols[i]).position)

        # delete rightmost column
        cols.remove(name)
        # create new Done column, so we can delete the other one
        self.client.post(reverse('kanbancol:create', kwargs={'project': self.short}), {'name': 'Done2', 'type': 'Done'})
        self.client.post(reverse('kanbancol:delete', kwargs={'project': self.short, 'position': 3}))
        for i in range(len(cols)):
            self.assertEqual(i, KanbanColumn.objects.get(name=cols[i]).position)

    def test_edit_delete_reject_last_todo_or_last_done_column(self):
        vals = {
            'name': "Testmodification",
            'type': 'InProgress',
        }
        response = self.client.post(reverse('kanbancol:update',
                                            kwargs={'position': 0, 'project': self.project.name_short}),
                                    vals)
        self.assertContains(response, 'edit rejected')
        response = self.client.post(reverse('kanbancol:update',
                                            kwargs={'position': 2, 'project': self.project.name_short}),
                                    vals)
        self.assertContains(response, 'edit rejected')
        response = self.client.post(reverse('kanbancol:delete',
                                            kwargs={'position': 0, 'project': self.project.name_short}),
                                    {'delete': 'true'},
                                    follow=True)
        self.assertContains(response, 'delete was rejected')
        response = self.client.post(reverse('kanbancol:delete',
                                            kwargs={'position': 2, 'project': self.project.name_short}),
                                    {'delete': 'true'},
                                    follow=True)
        self.assertContains(response, 'delete was rejected')
        response = self.client.post(reverse('kanbancol:delete',
                                            kwargs={'position': 1, 'project': self.project.name_short}),
                                    {'delete': 'true'},
                                    follow=True)
        self.assertNotContains(response, 'delete was rejected')

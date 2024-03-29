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

        cls.vals_testcolumn_todo = {
            'name': "Testcolumn",
            'type': 'ToDo',
            'project': cls.project.pk
        }
        cls.vals_testmodification = {
            'name': "Testmodification",
            'type': 'ToDo',
        }

    def setUp(self):
        self.client.force_login(self.user)
        # NOTE: these elements get modified by some testcases, so they should NOT be created in setUpTestData()

    def test_permission_functions(self):
        col = self.project.kanbancol.first()

        self.assertEqual(col.user_has_read_permissions(self.user), True)
        self.assertEqual(col.user_has_write_permissions(self.user), True)

        self.assertEqual(col.user_has_read_permissions(self.user2), True)
        self.assertEqual(col.user_has_write_permissions(self.user2), False)

    def test_cant_create_new_col_as_dev(self):
        self.client.force_login(self.user2)

        pre_num_cols = KanbanColumn.objects.count()
        user_doesnt_pass_test_and_gets_404(self, 'kanbancol:create', address_kwargs={'project': self.short},
                                           get_kwargs=self.vals_testcolumn_todo)
        self.assertEqual(KanbanColumn.objects.count(), pre_num_cols)

        self.client.force_login(self.user)

    def test_cant_update_col_as_dev(self):
        self.client.force_login(self.user2)

        pre_cols = list(KanbanColumn.objects.filter(project=self.project))
        user_doesnt_pass_test_and_gets_404(self, 'kanbancol:update',
                                           address_kwargs={'position': 3, 'project': self.short},
                                           get_kwargs=self.vals_testmodification)
        current_cols = list(KanbanColumn.objects.filter(project=self.project))
        self.assertEqual(current_cols, pre_cols)

        self.client.force_login(self.user)

    def test_cant_delete_col_as_dev(self):
        self.client.force_login(self.user2)

        pre_cols = list(KanbanColumn.objects.filter(project=self.project))
        user_doesnt_pass_test_and_gets_404(self, 'kanbancol:delete',
                                           address_kwargs={'position': 3, 'project': self.short},
                                           get_kwargs={'delete': 'true'})
        current_cols = list(KanbanColumn.objects.filter(project=self.project))
        self.assertEqual(current_cols, pre_cols)

        self.client.force_login(self.user)

    def test_cant_move_col_as_dev(self):
        self.client.force_login(self.user2)

        pre_cols = list(KanbanColumn.objects.filter(project=self.project))
        user_doesnt_pass_test_and_gets_404(self, 'kanbancol:movedown',
                                           address_kwargs={'project': self.short, 'position': 0})
        current_cols = list(KanbanColumn.objects.filter(project=self.project))
        self.assertEqual(current_cols, pre_cols)

        user_doesnt_pass_test_and_gets_404(self, 'kanbancol:moveup',
                                           address_kwargs={'project': self.short, 'position': 1})
        current_cols = list(KanbanColumn.objects.filter(project=self.project))
        self.assertEqual(current_cols, pre_cols)

        self.client.force_login(self.user)

    def test_up_and_down_view_post_request(self):
        pre_cols = list(KanbanColumn.objects.filter(project=self.project))
        # move down
        expected_cols = [*pre_cols[1:2], *pre_cols[0:1], *pre_cols[2:]]
        response = self.client.post(reverse('kanbancol:movedown', kwargs={'project': self.short, 'position': 0}),
                                    follow=True)
        self.assertEqual(response.status_code, 200)
        current_cols = list(KanbanColumn.objects.filter(project=self.project))
        self.assertEqual(current_cols, expected_cols)

        # move up
        expected_cols = pre_cols
        response = self.client.post(reverse('kanbancol:moveup', kwargs={'project': self.short, 'position': 1}),
                                    follow=True)
        self.assertEqual(response.status_code, 200)
        current_cols = list(KanbanColumn.objects.filter(project=self.project))
        self.assertEqual(current_cols, expected_cols)

    def test_up_down_view_get_request_404(self):
        # There are no kanban columns and hence a move is not possible
        response = self.client.get(reverse('kanbancol:movedown', kwargs={'project': self.short, 'position': 0}),
                                   follow=True)
        self.assertEqual(response.status_code, 404)

        response = self.client.get(reverse('kanbancol:moveup', kwargs={'project': self.short, 'position': 1}),
                                   follow=True)
        self.assertEqual(response.status_code, 404)

    def test_form_create(self):
        pre_cols = list(KanbanColumn.objects.filter(project=self.project))
        new_col = KanbanColumn(name=self.vals_testcolumn_todo['name'],
                               type=self.vals_testcolumn_todo['type'],
                               project=self.project)
        pre_num_len = len(pre_cols)
        # create
        response = self.client.post(reverse('kanbancol:create', kwargs={'project': self.short}),
                                    self.vals_testcolumn_todo)
        self.client.get(reverse("project:edit", kwargs={"project": self.short}))
        self.assertRedirects(response, reverse('project:edit', kwargs={'project': self.short}))

        response = self.client.get(response['location'])
        self.assertEqual(response.status_code, 200)
        # We always insert at the end
        # TODO this check should be part of a selenium TC
        self.assertEqual(response.context['columns'][3].name, "Testcolumn")
        self.assertEqual(str(response.context['columns'][3]), "Testcolumn")
        # TODO selenium TC end
        current_cols = list(KanbanColumn.objects.filter(project=self.project))
        current_num_len = len(current_cols)
        self.assertEqual(current_num_len, pre_num_len+1)
        self.assertEqual(current_cols[current_num_len-1].name, self.vals_testcolumn_todo['name'])

    def test_modify_column(self):
        pre_cols = list(KanbanColumn.objects.filter(project=self.project))
        # modify in progress column
        response = self.client.post(reverse('kanbancol:update', kwargs={'position': 1, 'project': self.short}),
                                    self.vals_testmodification)
        self.assertRedirects(response, reverse('project:edit', kwargs={'project': self.short}))

        response = self.client.get(response['location'])
        # TODO this is a check for selenium
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['columns'][1].name, self.vals_testmodification['name'])
        # TODO END
        current_cols = list(KanbanColumn.objects.filter(project=self.project))
        # the comparison of KanbanColumns doesn't take the name into account, hence the additional name and type check
        self.assertEqual(pre_cols, current_cols)
        self.assertEqual(current_cols[1].name, self.vals_testmodification['name'])
        self.assertEqual(current_cols[1].type, self.vals_testmodification['type'])

    def test_delete_column(self):
        pre_cols = list(KanbanColumn.objects.filter(project=self.project))
        expected_cols = [*pre_cols[0:1], *pre_cols[2:3]]

        # try to delete the column used in an issue (supposed to fail)
        response = self.client.post(reverse('kanbancol:delete', kwargs={'position': 1, 'project': self.short}),
                                    {'delete': 'true'})
        self.assertRedirects(response, reverse('project:edit', kwargs={'project': self.short}))
        current_cols = list(KanbanColumn.objects.filter(project=self.project))
        self.assertEqual(current_cols, expected_cols)

    def test_cant_change_type_of_last_done_col(self):
        pre_cols = list(KanbanColumn.objects.filter(project=self.project))
        expected_cols = pre_cols
        # modify last todo column (should fail)
        response = self.client.post(reverse('kanbancol:update', kwargs={'position': 0, 'project': self.short}),
                                    self.vals_testmodification)
        current_cols = list(KanbanColumn.objects.filter(project=self.project))
        self.assertEqual(current_cols, expected_cols)
        # delete last done column (should fail)
        response = self.client.post(reverse('kanbancol:delete', kwargs={'position': 0, 'project': self.short}),
                                    {'delete': 'true'})
        current_cols = list(KanbanColumn.objects.filter(project=self.project))
        self.assertEqual(current_cols, expected_cols)

    def test_cant_change_type_of_last_todo_col(self):
        pre_cols = list(KanbanColumn.objects.filter(project=self.project))
        expected_cols = pre_cols
        # modify last done column (should fail)
        response = self.client.post(reverse('kanbancol:update', kwargs={'position': 2, 'project': self.short}),
                                    self.vals_testmodification)
        current_cols = list(KanbanColumn.objects.filter(project=self.project))
        self.assertEqual(current_cols, expected_cols)
        # delete last done column (should fail)
        response = self.client.post(reverse('kanbancol:delete', kwargs={'position': 2, 'project': self.short}),
                                    {'delete': 'true'})
        current_cols = list(KanbanColumn.objects.filter(project=self.project))
        self.assertEqual(current_cols, expected_cols)

    def test_cant_delete_column_in_use(self):
        pre_cols = list(KanbanColumn.objects.filter(project=self.project))
        expected_cols = pre_cols
        # use the column in an issue
        issue = Issue(
            title="Test-Issue",
            kanbancol=KanbanColumn.objects.get(position=1, project__name_short=self.short),
            project=self.project, type="Bug"
        )
        issue.save()

        # try to delete the column used in an issue (supposed to fail)
        response = self.client.post(reverse('kanbancol:delete', kwargs={'position': 1, 'project': self.short}),
                                    {'delete': 'true'})
        self.assertRedirects(response, reverse('project:edit', kwargs={'project': self.short}))
        current_cols = list(KanbanColumn.objects.filter(project=self.project))
        self.assertEqual(current_cols, expected_cols)

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

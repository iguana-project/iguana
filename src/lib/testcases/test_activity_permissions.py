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
from django.contrib.auth import get_user_model
from project.models import Project
from django.urls.base import reverse
from actstream.models import actor_stream
from lib.activity_permissions import check_activity_permissions
from issue.models import Issue
from kanbancol.models import KanbanColumn


project_settings = {
    'name': 'test_project',
    'name_short': 'tp',
    'description': 'test',
}

issue_settings = {
    'title': "Test-Issue",
    'type': "Bug",
    'priority': 2,
    'storypoints': 0,
}


class TestActivityPermissions(TestCase):
    @classmethod
    def setUpTestData(cls):
        # NOTE: if you modify these elements they need to be created in setUp(), instead of here
        cls.user = get_user_model().objects.create_user('test', 'test@testing.com', 'test1234')
        cls.user2 = get_user_model().objects.create_user('foo', 'foo@testing.com', 'foo1234')

    def setUp(self):
        self.client.force_login(self.user)
        # NOTE: these elements get modified by some testcases, so they should NOT be created in setUpTestData()
        # create a default project
        project_settings["manager"] = (self.user.pk)
        self.client.post(reverse('project:create'), project_settings)
        self.project = Project.objects.filter(name_short=project_settings['name_short']).first()

        # create a kanban column for the issue
        self.column = KanbanColumn(name='Column', position=4, project=self.project)
        self.column.save()

        # create an issue
        issue_settings['kanbancol'] = self.column.pk
        self.client.post(reverse('issue:create', kwargs={'project': self.project.name_short}), issue_settings)
        self.issue = Issue.objects.filter(project=self.project.pk).first()

    def test_user_has_permissions(self):
        clean_actions = actor_stream(self.user)
        filtered_actions = check_activity_permissions(self.user, clean_actions)
        # the two query sets must be equal when the user has permissions on the issue/project
        self.assertQuerysetEqual(clean_actions, [a.__repr__() for a in filtered_actions])

    def test_user_has_no_permissions(self):
        self.client.force_login(self.user2)
        clean_actions = actor_stream(self.user)
        filtered_actions = check_activity_permissions(self.user2, clean_actions)
        # the filtered actions must be empty because the user2 has no permissions
        self.assertEqual(filtered_actions.count(), 0)
        pass

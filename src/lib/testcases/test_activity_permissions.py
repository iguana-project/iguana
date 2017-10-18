"""
Iguana (c) by Marc Ammon, Moritz Fickenscher, Lukas Fridolin,
Michael Gunselmann, Katrin Raab, Christian Strate

Iguana is licensed under a
Creative Commons Attribution-ShareAlike 4.0 International License.

You should have received a copy of the license along with this
work. If not, see <http://creativecommons.org/licenses/by-sa/4.0/>.
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
        # NOTE: if you modify those elements they need to be created in setUp, instead of here
        cls.user = get_user_model().objects.create_user('test', 'test@testing.com', 'test1234')
        cls.user2 = get_user_model().objects.create_user('foo', 'foo@testing.com', 'foo1234')

    def setUp(self):
        self.client.force_login(self.user)
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

"""
Iguana (c) by Marc Ammon, Moritz Fickenscher, Lukas Fridolin,
Michael Gunselmann, Katrin Raab, Christian Strate

Iguana is licensed under a
Creative Commons Attribution-ShareAlike 4.0 International License.

You should have received a copy of the license along with this
work. If not, see <http://creativecommons.org/licenses/by-sa/4.0/>.
"""
from django.test import TestCase
from model_mommy import mommy

from issue.models import Issue
from kanbancol.models import KanbanColumn
from project.models import Project
from sprint.models import Sprint
from tag.models import Tag
from django.contrib.auth import get_user_model


class CreateObjectsTest(TestCase):
    def test_createObjects(self):

        # create users
        numUsers = 20
        for i in range(numUsers):
            mommy.make_recipe('user_management.user')

        self.assertEqual(get_user_model().objects.count(), numUsers)

        # create projects
        numProjects = 25
        for i in range(numProjects):
            mommy.make_recipe('project.project')

        self.assertEqual(Project.objects.count(), numProjects)
        self.assertEqual(get_user_model().objects.count(), numUsers)
        for i in range(1, numProjects+1):
            p = Project.objects.get(pk=i)
            self.assertIn(p.creator, get_user_model().objects.all())

        numIssues = 40

        for i in range(numIssues):
            mommy.make_recipe('issue.issue')

        self.assertEqual(Issue.objects.count(), numIssues)

        numColumns = 2 * numProjects
        for i in range(numColumns):
            mommy.make_recipe('kanbancol.kanbancol')

        self.assertEqual(KanbanColumn.objects.count(), 3*numProjects + numColumns)

        for col in KanbanColumn.objects.all():
            self.assertIn(col.project, Project.objects.all())

        numTags = 10
        for i in range(numTags):
            mommy.make_recipe('tag.tag')

        self.assertEqual(Tag.objects.count(), numTags)

        numSprints = 5
        for i in range(numSprints):
            mommy.make_recipe('sprint.sprint')

        self.assertEqual(Sprint.objects.count(), numSprints)

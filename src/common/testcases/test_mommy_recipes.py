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

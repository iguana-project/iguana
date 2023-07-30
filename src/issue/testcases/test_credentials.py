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

from project.models import Project
from issue.models import Issue, Comment, Attachment
from django.contrib.auth import get_user_model


class IssueSearchTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        # NOTE: if you modify these elements they need to be created in setUp(), instead of here
        cls.user = get_user_model().objects.create_user('a', 'b', 'c')

    def setUp(self):
        # NOTE: these elements get modified by some testcases, so they should NOT be created in setUpTestData()
        self.project = Project(creator=self.user, name_short='PRJ')
        self.project.save()
        self.project.manager.add(self.user)

        # create issue, comment and attachment
        self.issue = Issue(title="Test-Issue",
                           project=self.project,
                           kanbancol=self.project.kanbancol.first(),
                           type="Bug")
        self.issue.save()

        self.comment = Comment(issue=self.issue, creator=self.user)
        self.comment.save()

        self.attachment = Attachment(issue=self.issue, creator=self.user)
        self.attachment.save()

    def test_check_credentials(self):
        for i in [self.project, self.issue, self.comment, self.attachment]:
            self.assertEqual(getattr(i, 'user_has_read_permissions')(self.user), 1)
            self.assertEqual(getattr(i, 'user_has_write_permissions')(self.user), 1)

        # remove write permissions
        user2 = get_user_model().objects.create_user('d', 'e', 'f')

        self.project.developer.add(self.user)
        self.project.manager.remove(self.user)
        self.comment.creator = user2
        self.comment.save()
        self.attachment.creator = user2
        self.attachment.save()

        # issue and project do distinguish between read and write permissions
        for i in [self.project, self.issue]:
            self.assertEqual(getattr(i, 'user_has_read_permissions')(self.user), 1)
            self.assertEqual(getattr(i, 'user_has_write_permissions')(self.user), 0)

        for i in [self.comment, self.attachment]:
            self.assertEqual(getattr(i, 'user_has_read_permissions')(self.user), 1)
            self.assertEqual(getattr(i, 'user_has_write_permissions')(self.user), 0)

        # remove read permissions
        self.project.developer.remove(self.user)

        for i in [self.project, self.issue, self.comment, self.attachment]:
            self.assertEqual(getattr(i, 'user_has_read_permissions')(self.user), 0)
            self.assertEqual(getattr(i, 'user_has_write_permissions')(self.user), 0)

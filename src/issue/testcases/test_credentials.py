"""
Iguana (c) by Marc Ammon, Moritz Fickenscher, Lukas Fridolin,
Michael Gunselmann, Katrin Raab, Christian Strate

Iguana is licensed under a
Creative Commons Attribution-ShareAlike 4.0 International License.

You should have received a copy of the license along with this
work. If not, see <http://creativecommons.org/licenses/by-sa/4.0/>.
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

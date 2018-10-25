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
from issue.models import Issue
from django.contrib.auth import get_user_model


class StripImgMetadataTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        # NOTE: if you modify those elements they need to be created in setUp, instead of here
        cls.user = get_user_model().objects.create_user('a', 'b', 'c')

    def setUp(self):
        self.client.force_login(self.user)
        self.project = Project(creator=self.user, name_short='PRJ')
        self.project.save()
        self.project.manager.add(self.user)
        self.project.developer.add(self.user)
        # TODO create issue

    def test_change_avatar(self):
        # TODO TESTCASE change avatar - picture stripping
        pass

    def test_comment_with_picture(self):
        # TODO TESTCASE comment with picture from issue-detail - picture stripping
        pass

    def test_file_upload_picture(self):
        # TODO TESTCASE attachment from issue-detail - picture stripping
        pass

    def test_change_user_profile_wo_default_avatar(self):
        # TODO TESTCASE create test that changes the user profile while the current avatar is not the default one
        #      this might produce some additional errors
        pass

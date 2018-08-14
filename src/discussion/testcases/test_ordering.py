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

from project.models import Project
from issue.models import Issue, Comment, Attachment
from discussion.models import Notification, Notitype
from django.contrib.auth import get_user_model


class OrderingTest(TestCase):
    short = 'proj'

    @classmethod
    def setUpTestData(cls):
        # NOTE: if you modify those elements they need to be created in setUp, instead of here
        cls.user1 = get_user_model().objects.create_user('user1', 'mail', 'c')
        cls.user2 = get_user_model().objects.create_user('user2', 'othermail', 'c')
        cls.project = Project(creator=cls.user1, name_short=cls.short)
        cls.project.save()
        cls.project.developer.add(cls.user1)
        cls.project.developer.add(cls.user2)
        cls.project.manager.add(cls.user1)

    def test_all_notitypes_work(self):
        # TODO TESTCASE for each notification verify that there is a notification created
        pass

    def test_latest_notification_on_top(self):
        # TODO TESTCASE create multiple issues
        # TODO TESTCASE verify that the latest is on top
        # TODO TESTCASE update older issue with mention etc.
        # TODO TESTCASE verify that the changed one is on top
        pass

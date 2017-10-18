"""
Iguana (c) by Marc Ammon, Moritz Fickenscher, Lukas Fridolin,
Michael Gunselmann, Katrin Raab, Christian Strate

Iguana is licensed under a
Creative Commons Attribution-ShareAlike 4.0 International License.

You should have received a copy of the license along with this
work. If not, see <http://creativecommons.org/licenses/by-sa/4.0/>.
"""
from django.test.testcases import TestCase
from django.urls.base import reverse
import json

from common.settings import BASE_DIR, MEDIA_ROOT
from django.contrib.auth import get_user_model
from project.models import Project


class MotifyNotificationPropsTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        # NOTE: if you modify this element it needs to be created in setUp, instead of here
        cls.user = get_user_model().objects.create_user('a', 'b', 'c')
        cls.project = Project(creator=cls.user, name_short='PRJ')
        cls.project.save()
        cls.project.developer.add(cls.user)

        cls.project2 = Project(creator=cls.user, name_short='PRO')
        cls.project2.save()

    def setUp(self):
        # NOTE: this element gets modified by some of those tests, so this shall NOT be created in setUpTestData()
        self.client.force_login(self.user)

    # TODO TESTCASE split this into smaller testcases
    # TODO especially as soon as there is also an existing support for activity-stream and discussion-app
    def test_modify_notifications(self):

        # assert no GET
        response = self.client.get(reverse('user_profile:toggle_notification', kwargs={"username": 'a'}),
                                   {},
                                   follow=True)
        self.assertEqual(response.status_code, 405)

        # all parameters must be set
        response = self.client.post(reverse('user_profile:toggle_notification', kwargs={"username": 'a'}),
                                    {},
                                    follow=True)
        self.assertEqual(response.status_code, 404)

        response = self.client.post(reverse('user_profile:toggle_notification', kwargs={"username": 'a'}),
                                    {'shn_p': 'BLUB'},
                                    follow=True)
        self.assertEqual(response.status_code, 404)

        # check invalid notitype
        response = self.client.post(reverse('user_profile:toggle_notification', kwargs={"username": 'a'}),
                                    {'shn_p': 'BLUB',
                                     'notiway': 'mail',
                                     'notitype': 'notexisting',
                                     'enabled': '1'},
                                    follow=True)
        self.assertEqual(response.status_code, 404)

        # check project existing check
        response = self.client.post(reverse('user_profile:toggle_notification', kwargs={"username": 'a'}),
                                    {'shn_p': 'PP',
                                     'notiway': 'mail',
                                     'notitype': 'NewIssue',
                                     'enabled': '1'},
                                    follow=True)
        self.assertEqual(response.status_code, 404)

        # check project membership check
        response = self.client.post(reverse('user_profile:toggle_notification', kwargs={"username": 'a'}),
                                    {'shn_p': 'PRO',
                                     'notiway': 'mail',
                                     'notitype': 'NewIssue',
                                     'enabled': '1'},
                                    follow=True)
        self.assertEqual(response.status_code, 404)

        # set NewIssue property to 1
        response = self.client.post(reverse('user_profile:toggle_notification', kwargs={"username": 'a'}),
                                    {'shn_p': 'PRJ',
                                     'notiway': 'mail',
                                     'notitype': 'NewIssue',
                                     'enabled': '1'},
                                    follow=False)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.user.get_preference('notify_mail'), '{"PRJ": ["NewIssue"]}')
        # check deserialized data
        self.assertEqual(json.loads(self.user.get_preference('notify_mail'))['PRJ'][0], "NewIssue")

        # set NewComment property to 1
        response = self.client.post(reverse('user_profile:toggle_notification', kwargs={"username": 'a'}),
                                    {'shn_p': 'PRJ',
                                     'notiway': 'mail',
                                     'notitype': 'NewComment',
                                     'enabled': '1'},
                                    follow=False)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.user.get_preference('notify_mail'), '{"PRJ": ["NewIssue", "NewComment"]}')
        self.assertEqual(json.loads(self.user.get_preference('notify_mail'))['PRJ'][1], "NewComment")

        # set inactive property to 0
        response = self.client.post(reverse('user_profile:toggle_notification', kwargs={"username": 'a'}),
                                    {'shn_p': 'PRJ',
                                     'notiway': 'mail',
                                     'notitype': 'NewAttachment',
                                     'enabled': '0'},
                                    follow=False)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.user.get_preference('notify_mail'), '{"PRJ": ["NewIssue", "NewComment"]}')
        self.assertEqual(json.loads(self.user.get_preference('notify_mail'))['PRJ'][1], "NewComment")

        # set active property to 1
        response = self.client.post(reverse('user_profile:toggle_notification', kwargs={"username": 'a'}),
                                    {'shn_p': 'PRJ',
                                     'notiway': 'mail',
                                     'notitype': 'NewIssue',
                                     'enabled': '1'},
                                    follow=False)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.user.get_preference('notify_mail'), '{"PRJ": ["NewIssue", "NewComment"]}')
        self.assertEqual(json.loads(self.user.get_preference('notify_mail'))['PRJ'][1], "NewComment")

        # set NewIssue property to 0
        response = self.client.post(reverse('user_profile:toggle_notification', kwargs={"username": 'a'}),
                                    {'shn_p': 'PRJ',
                                     'notiway': 'mail',
                                     'notitype': 'NewIssue',
                                     'enabled': '0'},
                                    follow=False)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.user.get_preference('notify_mail'), '{"PRJ": ["NewComment"]}')
        # check deserialized data
        self.assertEqual(json.loads(self.user.get_preference('notify_mail'))['PRJ'][0], "NewComment")

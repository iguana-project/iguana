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

from django.contrib.auth import get_user_model
from project.models import Project
from user_management.views import LoginView
from common.testcases.generic_testcase_helper import redirect_to_login_and_user_doesnt_pass_test


class MotifyNotificationPropsTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        # NOTE: if you modify these elements they need to be created in setUp(), instead of here
        cls.user = get_user_model().objects.create_user('a', 'b', 'c')
        cls.project = Project(creator=cls.user, name_short='PRJ')
        cls.project.save()
        cls.project.developer.add(cls.user)

        cls.project2 = Project(creator=cls.user, name_short='PRO')
        cls.project2.save()

    def setUp(self):
        self.client.force_login(self.user)
        # NOTE: these elements get modified by some testcases, so they should NOT be created in setUpTestData()

    # TODO TESTCASE split this into smaller testcases
    # TODO especially as soon as there is also an existing support for activity-stream and discussion-app
    def test_modify_notifications(self):

        # assert GET is not allowed; this fails due to two things:
        # 1. No GET is allowed (no function) and
        # 2. GET doesn't provide all required information and hence it fails already in the test_func()
        response = self.client.get(reverse('user_profile:toggle_notification', kwargs={"username": 'a'}),
                                   {'shn_p': 'PRJ',
                                    'notiway': 'mail',
                                    'notitype': 'NewIssue',
                                    'enabled': '1'},
                                   )
        self.assertEqual(response.status_code, 302)
        response = self.client.get(response['location'])
        # verify the login-required mixin
        self.assertEqual(response.resolver_match.func.__name__, LoginView.as_view().__name__)
        self.assertContains(response, 'Your account doesn\'t have access to this page.')

        # all parameters must be set; fails at the UserPassesTestMixin
        redirect_to_login_and_user_doesnt_pass_test(self, 'user_profile:toggle_notification',
                                                    address_kwargs={"username": 'a'}, get_kwargs={})
        redirect_to_login_and_user_doesnt_pass_test(self, 'user_profile:toggle_notification',
                                                    address_kwargs={"username": 'a'}, get_kwargs={'shn_p': 'BLUB'})

        # check invalid notitype
        response = self.client.post(reverse('user_profile:toggle_notification', kwargs={"username": 'a'}),
                                    {'shn_p': 'PRJ',
                                     'notiway': 'mail',
                                     'notitype': 'notexisting',
                                     'enabled': '1'},
                                    follow=True)
        self.assertEqual(response.status_code, 404)

        # check project existing check; fails at the UserPassesTestMixin
        redirect_to_login_and_user_doesnt_pass_test(self, 'user_profile:toggle_notification',
                                                    address_kwargs={"username": 'a'},
                                                    get_kwargs={'shn_p': 'PP',
                                                                'notiway': 'mail',
                                                                'notitype': 'NewIssue',
                                                                'enabled': '1'})

        # check project membership check; fails at the UserPassesTestMixin
        redirect_to_login_and_user_doesnt_pass_test(self, 'user_profile:toggle_notification',
                                                    address_kwargs={"username": 'a'},
                                                    get_kwargs={'shn_p': 'PRO',
                                                                'notiway': 'mail',
                                                                'notitype': 'NewIssue',
                                                                'enabled': '1'})

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

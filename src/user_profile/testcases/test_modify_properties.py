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
from common.testcases.generic_testcase_helper import redirect_to_login_and_user_doesnt_pass_test, \
        user_doesnt_pass_test_and_gets_404


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

        # successful address_kwargs
        cls.address_kwargs = {"username": 'a'}
        # successful get_kwargs
        # unfortunately pycodestyle doesn't allow noqa comments .... hence the ugly alignment
        cls.enable_NewAttachment = {'shn_p': 'PRJ',
                                    'notiway': 'mail',
                                    'notitype': 'NewAttachment',
                                    'enabled': '1'
                                    }
        cls.disable_NewAttachment = {'shn_p': 'PRJ',
                                     'notiway': 'mail',
                                     'notitype': 'NewAttachment',
                                     'enabled': '0'
                                     }
        cls.enable_NewComment = {'shn_p': 'PRJ',
                                 'notiway': 'mail',
                                 'notitype': 'NewComment',
                                 'enabled': '1'
                                 }
        cls.disable_NewComment = {'shn_p': 'PRJ',
                                  'notiway': 'mail',
                                  'notitype': 'NewComment',
                                  'enabled': '0'
                                  }
        cls.enable_NewIssue = {'shn_p': 'PRJ',
                               'notiway': 'mail',
                               'notitype': 'NewIssue',
                               'enabled': '1'
                               }
        cls.disable_NewIssue = {'shn_p': 'PRJ',
                                'notiway': 'mail',
                                'notitype': 'NewIssue',
                                'enabled': '0'
                                }
        cls.enable_NewComment_second_prj = {'shn_p': 'PRO',
                                            'notiway': 'mail',
                                            'notitype': 'NewComment',
                                            'enabled': '1'
                                            }

    def setUp(self):
        self.client.force_login(self.user)
        # NOTE: these elements get modified by some testcases, so they should NOT be created in setUpTestData()

    def test_notification_needs_post_request(self):
        # assert GET is not allowed; this fails due to two things:
        # 1. No GET is allowed (no function) and
        # 2. GET doesn't provide all required information and hence it fails already in the test_func()
        response = self.client.get(reverse('user_profile:toggle_notification', kwargs=self.address_kwargs),
                                   self.enable_NewIssue)
        self.assertEqual(response.status_code, 404)

    def test_notification_all_parameters_are_required(self):
        self.client.post(reverse('user_profile:toggle_notification', kwargs={"username": 'a'}),
                         self.enable_NewIssue, follow=False)
        pref = self.user.get_preference("notify_mail")
        # Only enabled for NewIssue
        self.assertEqual(pref, '{"PRJ": ["NewIssue"]}')

        # all parameters must be set; fails at the UserPassesTestMixin
        user_doesnt_pass_test_and_gets_404(self, 'user_profile:toggle_notification',
                                           address_kwargs=self.address_kwargs, get_kwargs={})
        user_doesnt_pass_test_and_gets_404(self, 'user_profile:toggle_notification',
                                           address_kwargs=self.address_kwargs, get_kwargs={'shn_p': 'BLUB'})
        # missing enabled
        missing_enabled = self.enable_NewIssue.copy()
        # it is fine to have ['enabled'] set to something other than 1 or 0 but it gets ignored then
        missing_enabled.pop('enabled')
        user_doesnt_pass_test_and_gets_404(self, 'user_profile:toggle_notification',
                                           address_kwargs=self.address_kwargs, get_kwargs=missing_enabled)
        self.assertEqual(pref, '{"PRJ": ["NewIssue"]}')

        # missing notitype
        missing_notitype = self.enable_NewIssue.copy()
        missing_notitype['notitype'] = ''
        user_doesnt_pass_test_and_gets_404(self, 'user_profile:toggle_notification',
                                           address_kwargs=self.address_kwargs, get_kwargs=missing_notitype)
        missing_notitype.pop('notitype')
        user_doesnt_pass_test_and_gets_404(self, 'user_profile:toggle_notification',
                                           address_kwargs=self.address_kwargs, get_kwargs=missing_notitype)
        self.assertEqual(pref, '{"PRJ": ["NewIssue"]}')

        # missing notiway
        missing_notiway = self.enable_NewIssue.copy()
        # it is fine to have ['notiway'] set to something other than 'mail' but it gets ignored then
        # because we want further options in the future
        missing_notiway.pop('notiway')
        user_doesnt_pass_test_and_gets_404(self, 'user_profile:toggle_notification',
                                           address_kwargs=self.address_kwargs, get_kwargs=missing_notiway)
        self.assertEqual(pref, '{"PRJ": ["NewIssue"]}')

        # missing shn_p
        missing_shn_p = self.enable_NewIssue.copy()
        missing_shn_p['shn_p'] = ''
        user_doesnt_pass_test_and_gets_404(self, 'user_profile:toggle_notification',
                                           address_kwargs=self.address_kwargs, get_kwargs=missing_shn_p)
        missing_shn_p.pop('shn_p')
        user_doesnt_pass_test_and_gets_404(self, 'user_profile:toggle_notification',
                                           address_kwargs=self.address_kwargs, get_kwargs=missing_shn_p)
        self.assertEqual(pref, '{"PRJ": ["NewIssue"]}')

    def test_notification_invalid_notitype(self):
        # check invalid notitype
        enable_notexisting = self.enable_NewIssue.copy()
        enable_notexisting['notitype'] = 'notexisting'
        response = self.client.post(reverse('user_profile:toggle_notification', kwargs={"username": 'a'}),
                                    enable_notexisting, follow=True)
        self.assertEqual(response.status_code, 404)

    def test_notification_insufficient_project_permissions(self):
        # check project existing check; fails at the UserPassesTestMixin
        wrong_project = self.enable_NewIssue.copy()
        wrong_project['shn_p'] = 'PP'
        user_doesnt_pass_test_and_gets_404(self, 'user_profile:toggle_notification',
                                           address_kwargs={"username": 'a'},
                                           get_kwargs=wrong_project)

        # check project membership check; fails at the UserPassesTestMixin
        wrong_project['shn_p'] = 'PRO'
        user_doesnt_pass_test_and_gets_404(self, 'user_profile:toggle_notification',
                                           address_kwargs={"username": 'a'},
                                           get_kwargs=wrong_project)

    def check_preferences(self, response, project, noti_types):
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.user.get_preference('notify_mail'),
                         '{"'+project+'": '+str(noti_types).replace("'", '"')+'}')
        # check deserialized data
        for i in range(len(noti_types)):
            self.assertEqual(json.loads(self.user.get_preference('notify_mail'))[project][i], noti_types[i])

    # user-profile mail-notification PRJ project for new comment
    def test_modify_notifications_by_mail_success_case_new_comment(self):
        # set NewIssue property to 1
        response = self.client.post(reverse('user_profile:toggle_notification', kwargs={"username": 'a'}),
                                    self.enable_NewComment, follow=False)
        self.check_preferences(response, "PRJ", ["NewComment"])

        # redo => shouldn't throw errors
        response = self.client.post(reverse('user_profile:toggle_notification', kwargs={"username": 'a'}),
                                    self.enable_NewComment, follow=False)
        self.check_preferences(response, "PRJ", ["NewComment"])

        # set NewIssue property to 0
        response = self.client.post(reverse('user_profile:toggle_notification', kwargs={"username": 'a'}),
                                    self.disable_NewComment, follow=False)
        # project key remains in list
        self.check_preferences(response, "PRJ", [])

        # redo => shouldn't throw errors
        response = self.client.post(reverse('user_profile:toggle_notification', kwargs={"username": 'a'}),
                                    self.disable_NewComment, follow=False)
        self.check_preferences(response, "PRJ", [])

    # user-profile mail-notification PRJ project for new issue
    def test_modify_notifications_by_mail_success_case_new_issue(self):
        # set NewIssue property to 1
        response = self.client.post(reverse('user_profile:toggle_notification', kwargs={"username": 'a'}),
                                    self.enable_NewIssue, follow=False)
        self.check_preferences(response, "PRJ", ["NewIssue"])

        # redo => shouldn't throw errors
        response = self.client.post(reverse('user_profile:toggle_notification', kwargs={"username": 'a'}),
                                    self.enable_NewIssue, follow=False)
        self.check_preferences(response, "PRJ", ["NewIssue"])

        # set NewIssue property to 0
        response = self.client.post(reverse('user_profile:toggle_notification', kwargs={"username": 'a'}),
                                    self.disable_NewIssue, follow=False)
        # project key remains in list
        self.check_preferences(response, "PRJ", [])

        # redo => shouldn't throw errors
        response = self.client.post(reverse('user_profile:toggle_notification', kwargs={"username": 'a'}),
                                    self.disable_NewIssue, follow=False)
        self.check_preferences(response, "PRJ", [])

    # user-profile mail-notification per project
    def test_modify_notifications_by_mail_success_case_enable_multiple(self):
        # set NewIssue property to 1
        response = self.client.post(reverse('user_profile:toggle_notification', kwargs={"username": 'a'}),
                                    self.enable_NewIssue, follow=False)
        self.check_preferences(response, "PRJ", ["NewIssue"])

        # set NewComment property to 1
        response = self.client.post(reverse('user_profile:toggle_notification', kwargs={"username": 'a'}),
                                    self.enable_NewComment, follow=False)
        self.check_preferences(response, "PRJ", ["NewIssue", "NewComment"])

        # set inactive property to 0 => shouldn't change anything and throw no errors
        response = self.client.post(reverse('user_profile:toggle_notification', kwargs={"username": 'a'}),
                                    self.disable_NewAttachment, follow=False)
        self.check_preferences(response, "PRJ", ["NewIssue", "NewComment"])

        # set NewComment property to 1 of second project
        self.project2.developer.add(self.user)
        self.project2.save()
        response = self.client.post(reverse('user_profile:toggle_notification', kwargs={"username": 'a'}),
                                    self.enable_NewComment_second_prj, follow=False)
        self.assertEqual(response.status_code, 302)
        noti_types_prj = ["NewIssue", "NewComment"]
        self.assertEqual(self.user.get_preference('notify_mail'),
                         '{"PRJ": ["NewIssue", "NewComment"], "PRO": ["NewComment"]}')
        # check deserialized data
        for i in range(len(noti_types_prj)):
            self.assertEqual(json.loads(self.user.get_preference('notify_mail'))["PRJ"][i], noti_types_prj[i])
        self.assertEqual(json.loads(self.user.get_preference('notify_mail'))["PRO"][0], "NewComment")

        # set NewComment property of PRJ to 0, should stay for PRO
        response = self.client.post(reverse('user_profile:toggle_notification', kwargs={"username": 'a'}),
                                    self.disable_NewComment, follow=False)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.user.get_preference('notify_mail'), '{"PRJ": ["NewIssue"], "PRO": ["NewComment"]}')
        # # check deserialized data
        self.assertEqual(json.loads(self.user.get_preference('notify_mail'))['PRJ'][0], "NewIssue")
        self.assertEqual(json.loads(self.user.get_preference('notify_mail'))['PRO'][0], "NewComment")

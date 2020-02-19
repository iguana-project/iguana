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

from django.contrib.auth import get_user_model
from project.models import Project
from issue.models import Issue
from discussion.models import Notification, Notitype
from django.core import mail
from django.core.mail import outbox
from common.settings import HOST
from common.tasks import send_discussion_mail

import json


class MailNotificationTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        # NOTE: if you modify these elements they need to be created in setUp(), instead of here
        cls.user1 = get_user_model().objects.create_user('user1', '', 'c')
        cls.user2 = get_user_model().objects.create_user('user2', 'othermail', 'c')

    def setUp(self):
        # NOTE: these elements get modified by some testcases, so they should NOT be created in setUpTestData()
        # notify user2 on new issues
        self.user2.set_preference("notify_mail", json.dumps({'PRJ': ['NewIssue']}))
        self.project = Project(creator=self.user1, name_short='PRJ', name='Project')
        self.project.save()
        self.project.developer.add(self.user1)
        self.project.developer.add(self.user2)
        self.project.manager.add(self.user1)

        self.issue1 = Issue(creator=self.user1, title='test', project=self.project)
        self.issue1.save()

    def test_workflow(self):
        self.assertEqual(len(Notification.objects.all()), 1)

        # mail to user2 should have been sent
        # TODO TESTCASE temporarily disabled due to failing build on jenkins
        # self.assertEqual(len(outbox), 1)

        # rcvmail = outbox[0]
        # self.assertEqual(rcvmail.subject, "[Iguana] Notification from project \"Project\"")
        # self.assertEqual(rcvmail.to, ['othermail'])
        # self.assertIn("Someone created issue \"test\".", rcvmail.body)
        # self.assertIn("If you want to see it, visit https://" + HOST + self.issue1.get_absolute_url(), rcvmail.body)

    def test_task(self):
        # test invalid pk
        self.assertEqual(send_discussion_mail(4711), 1)

        # test empty mail address
        noti = Notification(user=self.user1, issue=self.issue1)
        noti.save()
        ntype = Notitype(type='NewIssue')
        ntype.save()
        noti.type.add(ntype)
        self.assertEqual(send_discussion_mail(noti.pk), 2)

        # test no notification necessary
        self.user1.email = 'mail'
        self.user1.save()
        self.assertEqual(send_discussion_mail(noti.pk), 3)
        self.user1.set_preference('notify_mail', json.dumps({'PRJ': ['Mention', 'NewComment']}))
        self.assertEqual(send_discussion_mail(noti.pk), 3)

        # test mail send
        self.user1.set_preference('notify_mail', json.dumps({'PRJ': ['Mention', 'NewComment', 'NewIssue']}))
        self.assertEqual(send_discussion_mail(noti.pk), 0)
        # assert that last mail sent goes to user1
        self.assertEqual(mail.outbox[len(mail.outbox)-1].to, ['mail'])

    def test_leave_project(self):
        self.client.force_login(self.user2)
        self.user2.set_preference('notify_mail', json.dumps({'PRJ': ['Mention', 'NewComment', 'NewIssue']}))
        self.user1.set_preference('notify_mail', json.dumps({'PRJ': ['Mention', 'NewComment', 'NewIssue']}))

        props = json.dumps(self.user2.get_preference('notify_mail'))
        self.assertIn('PRJ', props)

        props = json.dumps(self.user1.get_preference('notify_mail'))
        self.assertIn('PRJ', props)

        response = self.client.post(reverse('project:leave', kwargs={'project': 'PRJ'}),
                                    {'delete': 'true'},
                                    follow=True)
        self.assertEqual(response.status_code, 200)

        self.assertNotIn(self.user2, self.project.manager.all())

        props = json.dumps(self.user2.get_preference('notify_mail'))
        self.assertNotIn('PRJ', props)

        props = json.dumps(self.user1.get_preference('notify_mail'))
        self.assertIn('PRJ', props)

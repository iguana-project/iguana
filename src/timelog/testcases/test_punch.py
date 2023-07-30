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
from django.urls import reverse
from django.utils.timezone import now
from datetime import timedelta

from project.models import Project
from issue.models import Issue
from kanbancol.models import KanbanColumn
from django.contrib.auth import get_user_model
from timelog.templatetags.filter import duration
from timelog.models import Timelog, Punch


class TimelogTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        # NOTE: if you modify these elements they need to be created in setUp(), instead of here
        cls.user = get_user_model().objects.create_user('test', 'test@testing.com', 'test1234')
        cls.user2 = get_user_model().objects.create_user('test2', 'test@testing2.com', 'test1234')
        cls.user.save()
        cls.user2.save()

    def setUp(self):
        self.client.force_login(self.user)
        # NOTE: these elements get modified by some testcases, so they should NOT be created in setUpTestData()
        self.project = Project(creator=self.user, name_short='PRJ')
        self.project.save()
        self.project.developer.add(self.user)
        self.project.developer.add(self.user2)
        self.kanbancol = KanbanColumn(project=self.project, position=4, name='test')
        self.kanbancol.save()
        self.issue = Issue(title='a very very very very very very very long issue title',
                           project=self.project,
                           due_date='2016-12-16',
                           kanbancol=self.kanbancol,
                           storypoints='3'
                           )
        self.issue.save()
        self.issue2 = Issue(title='issue title',
                            project=self.project,
                            due_date='2016-12-16',
                            kanbancol=self.kanbancol,
                            storypoints='3'
                            )
        self.issue2.save()
        self.issue.assignee.add(self.user)

    def test_view_and_template(self):
        # TODO TESTCASE
        pass

    def test_redirect_to_login_and_login_required(self):
        # TODO TESTCASE
        pass

    def test_punch_in_out_0(self):
        response = self.client.post(reverse('issue:punch',
                                            kwargs={"project": self.issue.project.name_short,
                                                    "sqn_i": self.issue.number
                                                    }), follow=True
                                    )
        self.assertEqual(Timelog.objects.filter(user=self.user, issue=self.issue).exists(), False)
        self.assertEqual(Punch.objects.filter(user=self.user, issue=self.issue).exists(), True)
        response = self.client.post(reverse('issue:punch',
                                            kwargs={"project": self.issue.project.name_short,
                                                    "sqn_i": self.issue.number
                                                    }), follow=True
                                    )
        self.assertEqual(Timelog.objects.filter(user=self.user, issue=self.issue).exists(), True)
        self.assertEqual(Punch.objects.filter(user=self.user, issue=self.issue).exists(), False)

    def test_punch_in_out_multiple_users_0(self):
        # mulitple users punch same issue
        response = self.client.post(reverse('issue:punch',
                                            kwargs={"project": self.issue.project.name_short,
                                                    "sqn_i": self.issue.number
                                                    }), follow=True
                                    )
        self.client.force_login(self.user2)
        response = self.client.post(reverse('issue:punch',
                                            kwargs={"project": self.issue.project.name_short,
                                                    "sqn_i": self.issue.number
                                                    }), follow=True
                                    )
        self.assertEqual(Punch.objects.filter(issue=self.issue).count(), 2)
        response = self.client.post(reverse('issue:punch',
                                            kwargs={"project": self.issue.project.name_short,
                                                    "sqn_i": self.issue.number
                                                    }), follow=True
                                    )
        self.assertEqual(Punch.objects.filter(issue=self.issue).count(), 1)
        self.client.force_login(self.user)
        response = self.client.post(reverse('issue:punch',
                                            kwargs={"project": self.issue.project.name_short,
                                                    "sqn_i": self.issue.number
                                                    }), follow=True
                                    )
        self.assertEqual(Punch.objects.filter(issue=self.issue).count(), 0)
        self.assertEqual(Timelog.objects.filter(issue=self.issue).count(), 2)

        self.issue.assignee.add(self.user)

    def test_punch_in_out(self):
        response = self.client.post(reverse('issue:punch',
                                            kwargs={"project": self.issue.project.name_short,
                                                    "sqn_i": self.issue.number
                                                    }), follow=True
                                    )
        self.assertEqual(Timelog.objects.filter(user=self.user, issue=self.issue).exists(), False)
        self.assertEqual(Punch.objects.filter(user=self.user, issue=self.issue).exists(), True)
        response = self.client.post(reverse('issue:punch',
                                            kwargs={"project": self.issue.project.name_short,
                                                    "sqn_i": self.issue.number
                                                    }), follow=True
                                    )
        self.assertContains(response, self.issue.get_ticket_identifier())
        self.assertEqual(Timelog.objects.filter(user=self.user, issue=self.issue).exists(), True)
        self.assertEqual(Punch.objects.filter(user=self.user, issue=self.issue).exists(), False)

    def test_punch_in_out_multiple_users(self):
        # mulitple users punch same issue
        response = self.client.post(reverse('issue:punch',
                                            kwargs={"project": self.issue.project.name_short,
                                                    "sqn_i": self.issue.number
                                                    }), follow=True
                                    )
        self.client.force_login(self.user2)
        response = self.client.post(reverse('issue:punch',
                                            kwargs={"project": self.issue.project.name_short,
                                                    "sqn_i": self.issue.number
                                                    }), follow=True
                                    )
        self.assertEqual(Punch.objects.filter(issue=self.issue).count(), 2)
        response = self.client.post(reverse('issue:punch',
                                            kwargs={"project": self.issue.project.name_short,
                                                    "sqn_i": self.issue.number
                                                    }), follow=True
                                    )
        self.assertEqual(Punch.objects.filter(issue=self.issue).count(), 1)
        self.client.force_login(self.user)
        response = self.client.post(reverse('issue:punch',
                                            kwargs={"project": self.issue.project.name_short,
                                                    "sqn_i": self.issue.number
                                                    }), follow=True
                                    )
        self.assertEqual(Punch.objects.filter(issue=self.issue).count(), 0)
        self.assertEqual(Timelog.objects.filter(issue=self.issue).count(), 2)

    def test_punch_in_on_multiple_issues_not_possible(self):
        # mulitple users punch same issue
        response = self.client.post(reverse('issue:punch',
                                            kwargs={"project": self.issue.project.name_short,
                                                    "sqn_i": self.issue.number
                                                    }), follow=True
                                    )
        response = self.client.post(reverse('issue:punch',
                                            kwargs={"project": self.issue2.project.name_short,
                                                    "sqn_i": self.issue2.number
                                                    }), follow=True
                                    )
        self.assertContains(response, self.issue.get_ticket_identifier())

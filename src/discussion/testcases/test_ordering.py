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

from project.models import Project
from issue.models import Issue, Comment, Attachment
from discussion.models import Notification, Notitype
from django.contrib.auth import get_user_model


class OrderingTest(TestCase):
    short = 'proj'

    @classmethod
    def setUpTestData(cls):
        # NOTE: if you modify these elements they need to be created in setUp(), instead of here
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

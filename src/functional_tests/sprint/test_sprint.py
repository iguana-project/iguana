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
from django.test import Client
from lib.selenium_test_case import SeleniumTestCase
from django.urls import reverse
import datetime
import time

from django.contrib.auth import get_user_model
from issue.models import Issue
from kanbancol.models import KanbanColumn
from project.models import Project


# TODO we might wanna test the href-links on those pages
class SprintTest(SeleniumTestCase):

    def setUp(self):
        self.user = get_user_model().objects.create_user('a', 'b', 'c')
        self.project = Project(name="Fancy Project", name_short="FYP", description="Fancy description",
                               creator=self.user)
        self.project.save()
        self.project.developer.add(self.user)
        self.project2 = Project(name="plain Project", name_short="plai", creator=self.user)
        self.project2.save()
        self.project2.developer.add(self.user)

        # Uses the cookie hack from:
        # https://stackoverflow.com/questions/22494583/login-with-code-when-using-liveservertestcase-with-django
        client = Client()
        client.login(username='a', password='c')
        self.cookie = client.cookies['sessionid']
        self.selenium.get("{}{}".format(self.live_server_url, reverse('invite_users:invite_users')))
        self.selenium.add_cookie({'name': 'sessionid', 'value': self.cookie.value, 'secure': False, 'path': '/'})
        self.selenium.refresh()

    def test_reachable_and_elements_exist(self):
        # TODO TESTCASE
        # TODO backlog
        # TODO edit sprint
        # TODO sprintboard
        pass

    def test_create_sprint(self):
        # TODO TESTCASE
        pass

    def test_edit_sprint(self):
        # TODO TESTCASE
        pass

    def test_assign_issue_to_sprint(self):
        # TODO TESTCASE
        pass

    def test_remove_issue_form_sprint(self):
        # TODO TESTCASE
        pass

    def test_start_sprint(self):
        # TODO TESTCASE
        pass

    def test_stop_sprint(self):
        # TODO TESTCASE
        pass

    def test_sprintboard(self):
        # TODO TESTCASE (switch cols)
        pass

    def test_backlog(self):
        # TODO TESTCASE
        pass

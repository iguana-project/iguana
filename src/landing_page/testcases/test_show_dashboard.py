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
from django.urls.base import reverse

from django.contrib.auth import get_user_model
from landing_page.views import HomeView
from common.testcases.generic_testcase_helper import view_and_template, redirect_to_login_and_login_required


testUserName = "test"
testUserPassword = "test1234"
testUserEmail = "test@testing.com"


class ShowDashboardTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        # NOTE: if you modify these elements they need to be created in setUp(), instead of here
        cls.user = get_user_model().objects.create_user(testUserName, testUserEmail, testUserPassword)

    def setUp(self):
        self.client.force_login(self.user)
        # NOTE: these elements get modified by some testcases, so they should NOT be created in setUpTestData()

    def test_view_and_template(self):
        view_and_template(self, HomeView, 'landing_page/dashboard.html', 'landing_page:home')

    def test_redirect_to_login_and_login_required(self):
        self.client.logout()
        # when logged out there is no redirect but the template landingpage/home is used
        # since redirect_to_login_and_login_required() expects 302 we also use view_and_template here
        # this doesn't exactly represent the name of the testcase but the essential behaviour is similar
        view_and_template(self, HomeView, 'landing_page/home.html', 'landing_page:home')

    def test_show_dashboard_when_logged_in(self):
        response = self.client.get(reverse('landing_page:home'))
        self.assertTemplateUsed(response, "landing_page/dashboard.html")
        self.assertEqual(response.status_code, 200)

    def test_only_own_stuff_visible(self):
        # TODO TESTCASE
        pass

    def test_issue_list(self):
        # TODO TESTCASE tests for Issue-list
        pass

    def test_project_list(self):
        # TODO TESTCASE for project-list
        pass

# TODO TESTCASE additional tests for future stuff shown in the activity-sream

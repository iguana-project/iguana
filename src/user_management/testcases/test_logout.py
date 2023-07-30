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
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic.base import View
from django.urls import set_urlconf
from importlib import import_module, reload
import sys

from user_management.views import LoginView, LogoutView
from landing_page.views import HomeView
from django.contrib.auth import get_user_model
from django.conf import settings
from django.conf.urls import url
from user_management.urls import urlpatterns
from common.testcases.generic_testcase_helper import view_and_template, redirect_to_login_and_login_required


class LogoutTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        # NOTE: if you modify these elements they need to be created in setUp(), instead of here
        cls.user = get_user_model().objects.create_user('django', 'django@example.com', 'unchained')

    def test_view_and_template(self):
        # TODO TESTCASE see invite_users
        #      use view_and_template()
        # TODO LogoutView - logout
        pass

    def test_redirect_to_login_and_login_required(self):
        self.client.logout()
        # TODO TESTCASE see invite_users
        #      redirect_to_login_and_login_required()
        # TODO which views?
        # TODO LogoutView - logout
        pass

    def test_functionality(self):
        # TODO TESTCASE implement some testcases
        pass

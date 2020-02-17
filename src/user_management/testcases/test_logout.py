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
        # NOTE: if you modify this element it needs to be created in setUp, instead of here
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

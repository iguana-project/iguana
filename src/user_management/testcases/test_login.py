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


# creates a temporary view to be able to test the ?next= argument
def createTempViewURL():
    # add the TempView to the urlpatterns
    global urlpatterns
    urlpatterns += [
        url(r'^temp/?', TempView.as_view(), name='temp'),
    ]

    # reload the urlpatterns
    urlconf = settings.ROOT_URLCONF
    if urlconf in sys.modules:
        reload(sys.modules[urlconf])
    reloaded = import_module(urlconf)
    reloaded_urls = getattr(reloaded, 'urlpatterns')
    set_urlconf(tuple(reloaded_urls))

    # return the temporary URL
    return reverse('temp')


class TempView(LoginRequiredMixin, View):
    """
    Temporary view class that requires the user to be logged in.
    """
    pass


username = 'django'
email = 'django@example.com'
password = 'unchained'


class LoginTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        # NOTE: if you modify these elements they need to be created in setUp(), instead of here
        cls.user = get_user_model().objects.create_user(username, email, password)

    def test_login_view_and_template(self):
        view_and_template(self, LoginView, 'registration/login.html', 'login')

        response = self.client.post(reverse('login'), {'username': username, 'password': password})
        self.assertEqual(response.resolver_match.func.__name__, LoginView.as_view().__name__)

    # tests if the login/?next= -parameter is correct, therefore we use our dummy view, to be independent
    # from our implementation
    def test_nologin(self):
        tempURL = createTempViewURL()
        response = self.client.get(tempURL)
        self.assertEqual(response['location'], "/login/?next=" + tempURL)

    def login_with_get_request_disabled(self):
        response = self.client.get(reverse('login'), {'username': username, 'password': password}, follow=True)
        self.assertEqual(response.status_code, 200)
        # didn't login successfully
        self.assertTemplateUsed(response, 'landing_page:login.html')
        self.assertFalse(self.user.is_authenticated)

    # check whether login process works
    def test_login(self):
        response = self.client.post(reverse('login'), {'username': username, 'password': password}, follow=True)
        try:
            self.assertRedirects(response, reverse('landing_page:home'))
        except AssertionError:
            self.assertRedirects(response, reverse('landing_page:home')+'/')

        response = self.client.get(reverse('landing_page:home'))
        self.assertTemplateUsed(response, 'landing_page/dashboard.html')
        self.assertEqual(response.resolver_match.func.__name__, HomeView.as_view().__name__)
        self.assertEqual(response.status_code, 200)

    def test_logout_while_logged_in(self):
        self.client.force_login(self.user)

        response = self.client.get(reverse('logout'), follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.resolver_match.func.__name__, LogoutView.as_view().__name__)
        self.assertTemplateUsed(response, 'registration/login.html')

        tempURL = createTempViewURL()
        response = self.client.get(tempURL)
        self.assertEqual(response['location'], "/login/?next=" + tempURL)

    def test_logout_while_logged_out(self):
        response = self.client.get(reverse('logout'), follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.resolver_match.func.__name__, LogoutView.as_view().__name__)
        self.assertTemplateUsed(response, 'registration/login.html')

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
from django.core import mail

from django.contrib.auth import get_user_model

from user_management.views import PasswordResetView, PasswordResetSuccessView
from common.testcases.generic_testcase_helper import view_and_template, redirect_to_login_and_login_required

username = 'test'
email = 'test@testing.com'
password = 'test1234'
pw_reset_template = 'registration/password_reset_form.html'
pw_reset_conf_template = 'registration/password_reset_confirm.html'
pw_reset_comp_template = 'registration/password_reset_complete.html'
pw_reset_done_template = 'registration/password_reset_done.html'
dashboard_template = 'landing_page/dashboard.html'


class PasswordResetTest(TestCase):
    def setUp(self):
        # NOTE: these elements get modified by some testcases, so they should NOT be created in setUpTestData()
        self.user = get_user_model().objects.create_user(username, email, password)

    def test_view_and_template(self):
        # this tests only the get requests
        # PasswordResetView
        view_and_template(self, PasswordResetView, pw_reset_template, 'password_reset')
        # PasswordResetSuccessView
        view_and_template(self, PasswordResetSuccessView, pw_reset_done_template, 'password_reset_done')

        # TODO TESTCASE VerifyEmailAddress - this requires a post request

    # there is no test_redirect_to_login_and_login_required() because the actual use of this view
    # is to provide logged out
    def test_redirect_to_login_and_login_NOT_required(self):
        self.client.logout()
        # PasswordResetView
        response = self.client.get(reverse('password_reset'))
        self.assertContains(response, "Forgot your password? Enter your email address below, " +
                            "and we'll email instructions for setting a new one.")
        # PasswordResetSuccessView
        response = self.client.get(reverse('password_reset_done'))
        self.assertContains(response, "We've emailed instructions to you for setting your password.")

        # TODO TESTCASE VerifyEmailAddress - this requires a post request

    def test_post_mail_get_response_set_new_password(self):
        response = self.client.post(reverse('password_reset'), {'email': email})
        self.assertEqual(response.status_code, 302)

        # email sent assert
        self.assertEqual(len(mail.outbox), 1)
        token = response.context[0]['token']
        uid = response.context[0]['uid']

        response = self.client.get(reverse('password_reset_confirm', kwargs={'token': token, 'uidb64': uid}),
                                   follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, pw_reset_conf_template)
        self.assertRedirects(response, '/reset/%s/set-password/' % uid)

        new_password = 'new_pass12345'
        response = self.client.post(
            '/reset/%s/set-password/' % uid,
            {'new_password1': new_password, 'new_password2': new_password}, follow=True
        )
        self.assertTemplateUsed(response, pw_reset_comp_template)

        response = self.client.post(reverse('login'), {'username': username, 'password': new_password}, follow=True)
        self.assertTemplateUsed(response, dashboard_template)

    def test_reset_password_with_get_request_disabled(self):
        response = self.client.get(reverse('password_reset'), {'email': email}, follow=True)
        self.assertEqual(response.status_code, 200)
        # didn't send successfully
        self.assertTemplateUsed(response, pw_reset_template)

    def test_password_reset_done_template(self):
        # NOTE: somehow a follow=True results in a wrong mail-outbox therefore we need to duplicate this
        response = self.client.post(reverse('password_reset'), {'email': email}, follow=True)
        self.assertTemplateUsed(response, pw_reset_done_template)

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
from django.contrib.auth import get_user_model
from django.core import mail
from django.test import TestCase
from django.urls import reverse
import os
import re

from user_management.views import SignUpView
from landing_page.views import HomeView

from django.conf import settings
from django.test.utils import override_settings
from common.testcases.generic_testcase_helper import view_and_template, redirect_to_login_and_login_required


username = 'a'
email = 'a@a.com'
password = 'a1234568'
sign_up_dict = {'username': username, 'email': email, 'password1': password, 'password2': password,
                'captcha_0': 'PASSED', 'captcha_1': 'PASSED'}


class SignUpTest(TestCase):

    def test_view_and_template(self):
        view_and_template(self, SignUpView, 'registration/sign_up.html', 'sign_up')

        # TODO uses post maybe this can be merged into the view_and_template?
        response = self.client.post(reverse('sign_up'), sign_up_dict)
        self.assertEqual(response.resolver_match.func.__name__, SignUpView.as_view().__name__)

        # TODO TESTCASE VerifyEmailAddress - verify_email

    def test_email_verification_view_and_template(self):
        # trigger email
        self.client.post(reverse('sign_up'), sign_up_dict, follow=True)
        # TODO fix replacement of example.com as soon as the dev-settings are fixed
        temp_activation_link = re.findall("https://.*/activate/.*/.*", mail.outbox[0].body)[0][len("https://"):]
        local_activation_link = temp_activation_link.replace("example.com", "")

        response = self.client.get(local_activation_link, follow=True)
        self.assertContains(response, "Thanks for registering. You are now logged in.")
        self.assertTrue(get_user_model().objects.filter(username=username)[0].is_active)
        try:
            self.assertRedirects(response, reverse('landing_page:home'))
        except TypeError:
            self.assertRedirects(response, reverse('landing_page:home')+'/')
        self.assertEqual(response.resolver_match.func.__name__, HomeView.as_view().__name__)

    def test_creation_disabled_for_get_request(self):
        response = self.client.get(reverse('sign_up'), sign_up_dict)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'registration/sign_up.html')

    def test_sign_up(self):
        response = self.client.post(reverse('sign_up'), sign_up_dict, follow=True)

        self.assertContains(response, "Confirm your email address")
        # verify an email has been sent
        self.assertEqual(len(mail.outbox), 1)
        # TODO fix replacement of example.com as soon as the dev-settings are fixed
        temp_activation_link = re.findall("https://.*/activate/.*/.*", mail.outbox[0].body)[0][len("https://"):]
        local_activation_link = temp_activation_link.replace("example.com", "")

        response = self.client.get(local_activation_link, follow=True)
        self.assertNotContains(response, "Invalid")

        self.assertTrue(get_user_model().objects.filter(username=username)[0].is_active)

        # activation link is valid only once
        response = self.client.get(local_activation_link, follow=True)
        self.assertContains(response, "Invalid")
        self.assertTemplateUsed(response, "registration/invalid_activation_link.html")

    def test_random_url(self):
        # trigger email
        self.client.post(reverse('sign_up'), sign_up_dict, follow=True)

        response = self.client.get("/activate/MzY/0yk-quohp9bujoghuo6teizo", follow=True)
        self.assertContains(response, "Invalid")
        self.assertTemplateUsed(response, "registration/invalid_activation_link.html")
        self.assertFalse(get_user_model().objects.filter(username=username)[0].is_active)

    # helper function
    def sign_up_used(self, response):
        self.assertTemplateUsed(response, 'registration/sign_up.html')
        self.assertEqual(response.status_code, 200)

    def test_form(self):
        # email
        response = self.client.post(reverse('sign_up'), {'username': username,
                                                         'password1': password, 'password2': password,
                                                         'captcha_0': "PASSED", 'captcha_1': "PASSED"}, follow=True)
        self.sign_up_used(response)
        self.assertFormError(response, 'form', 'email', 'This field is required.')

        # username
        response = self.client.post(reverse('sign_up'), {'email': email,
                                                         'password1': password, 'password2': password,
                                                         'captcha_0': "PASSED", 'captcha_1': "PASSED"}, follow=True)
        self.sign_up_used(response)
        self.assertFormError(response, 'form', 'username', 'This field is required.')

        # password required
        response = self.client.post(reverse('sign_up'), {'email': email, 'username': username,
                                                         'password2': password,
                                                         'captcha_0': "PASSED", 'captcha_1': "PASSED"}, follow=True)
        self.sign_up_used(response)
        self.assertFormError(response, 'form', 'password1', 'This field is required.')
        response = self.client.post(reverse('sign_up'), {'email': email, 'username': username,
                                                         'password1': password,
                                                         'captcha_0': "PASSED", 'captcha_1': "PASSED"}, follow=True)
        self.sign_up_used(response)
        self.assertFormError(response, 'form', 'password2', 'This field is required.')

        # password similar
        response = self.client.post(reverse('sign_up'), {'email': email, 'username': username,
                                                         'password1': password, 'password2': 'b1234567',
                                                         'captcha_0': "PASSED", 'captcha_1': "PASSED"}, follow=True)
        self.sign_up_used(response)
        self.assertFormError(response, 'form', 'password2', "The two password fields didn't match.")

    # verify that username and email address of registered users are leaked only
    # if the captcha has been solved correctly
    def test_username_and_email_protected_with_captcha(self):
        new_user = get_user_model().objects.create_user(username=username, email=email, password=password)
        new_user.save()

        # empty captcha tests
        self.captcha_protects_username_and_email()
        self.captcha_does_not_hide_forbidden_at_element_in_username()

        # wrong captcha tests
        wrong_captcha = "WRONG_CAPTCHA"
        self.captcha_protects_username_and_email(wrong_captcha)
        self.captcha_does_not_hide_forbidden_at_element_in_username(wrong_captcha)

    def get_csrf_token(self):
        # extract the csrf token so only the captcha is not valid
        response = self.client.get(reverse('sign_up'))
        content = response.content.decode()
        csrf_token_index = content.index("csrfmiddlewaretoken")
        csrf_token = re.findall(r"value=['\"]{1}.*['\"]{1}", content[csrf_token_index:])[0]
        return csrf_token

    def captcha_protects_username_and_email(self, captcha=None):
        csrf_token = self.get_csrf_token()
        payload = {'username': username, 'email': email, 'password1': password, 'password2': password,
                   "csrfmiddlewaretoken": csrf_token}
        if captcha:
            payload['captcha_0'] = captcha
            payload['captcha_1'] = captcha

        response = self.client.post(reverse('sign_up'), payload)
        # neither the email nor the username of the already existing user is leaked as long as
        # the captcha has not been solved successfully
        self.assertNotContains(response, "User with this Email address already exists.")
        self.assertNotContains(response, "A user with that username already exists.")

    def captcha_does_not_hide_forbidden_at_element_in_username(self, captcha=None):
        csrf_token = self.get_csrf_token()
        username_with_at = username+"@foo"
        payload = {'username': username_with_at, 'email': email, 'password1': password, 'password2': password,
                   "csrfmiddlewaretoken": csrf_token}
        if captcha:
            payload['captcha_0'] = captcha
            payload['captcha_1'] = captcha

        response = self.client.post(reverse('sign_up'), payload)
        # the error message for forbidden at-elements in the username shall be shown regardless of the wrong captcha
        non_critical_user_err_msg = ("@ is not allowed in username. Username is required as 150 characters or " +
                                     "fewer. Letters, digits and ./+/-/_ only.")
        self.assertContains(response, non_critical_user_err_msg)

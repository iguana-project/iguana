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

from invite_users.views import InviteUserView, SuccessView
from user_management.views import LoginView
from django.contrib.auth import get_user_model, login
from common.testcases.generic_testcase_helper import view_and_template, redirect_to_login_and_login_required


class InviteUsersTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        # NOTE: if you modify these elements they need to be created in setUp(), instead of here
        cls.user = get_user_model().objects.create_user('a', 'a@a.com', 'a1234568')

    def setUp(self):
        self.client.force_login(self.user)
        # NOTE: these elements get modified by some testcases, so they should NOT be created in setUpTestData()

    def test_view_and_template(self):
        # invite_users
        view_and_template(self, InviteUserView, 'invite_users/invite_users.html', 'invite_users:invite_users')

        # successfully_invited
        view_and_template(self, SuccessView, 'invite_users/successfully_invited.html',
                          'invite_users:successfully_invited')

    def test_redirect_to_login_and_login_required(self):
        self.client.logout()
        redirect_to_login_and_login_required(self, 'invite_users:invite_users')
        redirect_to_login_and_login_required(self, 'invite_users:successfully_invited')

    def test_form(self):
        response = self.client.get(reverse('invite_users:invite_users'))
        form_data = {
            'form-TOTAL_FORMS': '1',
            'form-INITIAL_FORMS': '0',
            'form-MIN_NUM_FORMS': '1',
            'form-MAX_NUM_FORMS': '15',
            'form-0-email': '',
            'additional_message': '',
        }
        response = self.client.post(reverse('invite_users:invite_users'), form_data)
        self.assertFormsetError(response, 'formset', 0, 'email', 'This field is required.')
        self.invite_users_used(response)

        response = self.client.get(reverse('invite_users:invite_users'))
        form_data = {
            'form-TOTAL_FORMS': '4',
            'form-INITIAL_FORMS': '0',
            'form-MIN_NUM_FORMS': '1',
            'form-MAX_NUM_FORMS': '15',
            'form-0-email': '',
            'form-1-email': '',
            'form-2-email': '',
            'form-3-email': '',
            'additional_message': '',
        }
        response = self.client.post(reverse('invite_users:invite_users'), form_data)
        self.assertFormsetError(response, 'formset', 0, 'email', 'This field is required.')
        self.invite_users_used(response)

    def test_get_request_disabled_for_invitation(self):
        response = self.client.get(reverse('invite_users:invite_users'), {'form-0-email': 'b@b.com'})
        self.assertEqual(response.status_code, 200)
        # didn't invite successfully
        self.assertTemplateUsed(response, 'invite_users/invite_users.html')

    # helper function
    def invite_users_used(self, response):
        self.assertTemplateUsed(response, 'invite_users/invite_users.html')
        self.assertEqual(response.status_code, 200)

    def test_invite_one_user(self):
        response = self.client.get(reverse('invite_users:invite_users'))
        e0 = 'b@b.com'
        form_data = {
            'form-TOTAL_FORMS': '1',
            'form-INITIAL_FORMS': '0',
            'form-MIN_NUM_FORMS': '1',
            'form-MAX_NUM_FORMS': '15',
            'form-0-email': e0,
            'additional_message': '',
        }
        response = self.client.post(reverse('invite_users:invite_users'), form_data, follow=True)
        self.assertRedirects(response, 'successfully_invited')
        self.assertContains(response, e0)

    def test_multiple_user(self):
        response = self.client.get(reverse('invite_users:invite_users'))
        e0 = 'b@b.com'
        e1 = 'd@d.com'
        form_data = {
            'form-TOTAL_FORMS': '2',
            'form-INITIAL_FORMS': '0',
            'form-MIN_NUM_FORMS': '1',
            'form-MAX_NUM_FORMS': '15',
            'form-0-email': e0,
            'form-1-email': e1,
            'additional_message': '',
        }
        response = self.client.post(reverse('invite_users:invite_users'), form_data, follow=True)
        self.assertRedirects(response, 'successfully_invited')
        self.assertContains(response, e0)
        self.assertContains(response, e1)

    def test_successfully_invited(self):
        self.client.logout()
        response = self.client.get(reverse('invite_users:successfully_invited'), follow=True)
        self.assertContains(response, "Please login to see this page.")
        self.assertEqual(response.resolver_match.func.__name__, LoginView.as_view().__name__)

        self.client.force_login(self.user)
        response = self.client.get(reverse('invite_users:successfully_invited'))
        self.assertContains(response, "You didn't even invite anyone.")
        self.assertTemplateUsed(response, 'invite_users/successfully_invited.html')
        self.assertEqual(response.resolver_match.func.__name__, SuccessView.as_view().__name__)
        self.assertEqual(response.status_code, 200)

        response = self.client.get(reverse('invite_users:invite_users'))
        emails = ['a@a.com', 'a@b.com', 'a@c.com', 'a@d.com', 'b@a.com', 'b@b.com', 'b@c.com',
                  'c@a.com', 'c@b.com', 'c@c.com', 'd@a.com']
        form_data = {
            'form-TOTAL_FORMS': '11',
            'form-INITIAL_FORMS': '0',
            'form-MIN_NUM_FORMS': '1',
            'form-MAX_NUM_FORMS': '15',
            'additional_message': '',
        }
        for i in range(len(emails)):
            form_data['form-{}-email'.format(i)] = emails[i]
        response = self.client.post(reverse('invite_users:invite_users'), form_data, follow=True)
        self.assertTemplateUsed(response, 'invite_users/successfully_invited.html')
        self.assertContains(response, "You successfully invited")
        for email in emails:
            self.assertContains(response, email)

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
import os

from user_management.views import SignUpView
from landing_page.views import HomeView

from django.conf import settings
from django.test.utils import override_settings


username = 'a'
email = 'a@a.com'
password = 'a1234568'
sign_up_dict = {'username': username, 'email': email, 'password1': password, 'password2': password,
                'captcha_0': 'PASSED', 'captcha_1': 'PASSED'}


class SignUpTest(TestCase):

    def test_sign_up_view_and_template(self):
        response = self.client.get(reverse('sign_up'))
        self.assertTemplateUsed(response, 'registration/sign_up.html')

        response = self.client.post(reverse('sign_up'), sign_up_dict)
        self.assertEqual(response.resolver_match.func.__name__, SignUpView.as_view().__name__)

    def test_creation_disabled_for_get_request(self):
        response = self.client.get(reverse('sign_up'), sign_up_dict)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'registration/sign_up.html')

    def test_sign_up(self):
        response = self.client.post(reverse('sign_up'), sign_up_dict, follow=True)
        try:
            self.assertRedirects(response, reverse('landing_page:home'))
        except:
            self.assertRedirects(response, reverse('landing_page:home')+'/')

        self.assertEqual(response.resolver_match.func.__name__, HomeView.as_view().__name__)
        self.assertTemplateUsed(response, 'landing_page/dashboard.html')

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

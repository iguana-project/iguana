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

from invite_users.views import InviteUserView, SuccessView
from user_management.views import LoginView
from django.contrib.auth import get_user_model, login


class InviteUsersTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        # NOTE: if you modify this element it needs to be created in setUp, instead of here
        cls.user = get_user_model().objects.create_user('a', 'a@a.com', 'a1234568')

    def setUp(self):
        self.client.force_login(self.user)

    def test_invite_users_and_successfully_invited_view_and_template(self):
        # invite_users
        response = self.client.get(reverse('invite_users:invite_users'), follow=True)
        self.assertTemplateUsed(response, 'invite_users/invite_users.html')
        self.assertEqual(response.resolver_match.func.__name__, InviteUserView.as_view().__name__)

        # successfully_invited
        response = self.client.get(reverse('invite_users:successfully_invited'))
        self.assertTemplateUsed(response, 'invite_users/successfully_invited.html')
        self.assertEqual(response.resolver_match.func.__name__, SuccessView.as_view().__name__)

    def test_redirect_to_login_and_login_required(self):
        self.client.logout()
        response = self.client.get(reverse('invite_users:invite_users'))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['location'], '/login/?next=' + reverse('invite_users:invite_users'))
        response = self.client.get(response['location'])
        # verify the login-required mixin
        self.assertEqual(response.resolver_match.func.__name__, LoginView.as_view().__name__)
        self.assertContains(response, 'Please login to see this page.')

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

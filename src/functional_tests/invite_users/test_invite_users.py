"""
Iguana (c) by Marc Ammon, Moritz Fickenscher, Lukas Fridolin,
Michael Gunselmann, Katrin Raab, Christian Strate

Iguana is licensed under a
Creative Commons Attribution-ShareAlike 4.0 International License.

You should have received a copy of the license along with this
work. If not, see <http://creativecommons.org/licenses/by-sa/4.0/>.
"""
from django.test import Client
from lib.selenium_test_case import StaticSeleniumTestCase
from django.urls import reverse
import os

from django.contrib.auth import get_user_model
from django.conf import settings
from django.test.utils import override_settings


# TODO TESTCASE we might wanna test the href-links on those pages
class InviteUsersTest(StaticSeleniumTestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user('a_user', 'a@a.com', 'a1234568')
        # Uses the cookie hack from:
        # https://stackoverflow.com/questions/22494583/login-with-code-when-using-liveservertestcase-with-django
        client = Client()
        client.login(username='a_user', password='a1234568')
        self.cookie = client.cookies['sessionid']
        self.selenium.get("{}{}".format(self.live_server_url, reverse('invite_users:invite_users')))
        self.selenium.add_cookie({'name': 'sessionid', 'value': self.cookie.value, 'secure': False, 'path': '/'})
        self.selenium.refresh()

    def test_reachable_and_elements_exist(self):
        self.selenium.get("{}{}".format(self.live_server_url, reverse('invite_users:invite_users')))
        self.assertNotIn('Not Found', self.selenium.page_source)
        self.assertIn('Invite new User via email', self.selenium.title)
        self.assertIn('additional message', self.selenium.page_source)
        self.assertIn('email of person to be invited', self.selenium.page_source)
        invite_form = self.selenium.find_element_by_id('invite_friend_form')
        message = invite_form.find_element_by_id('id_additional_message')
        email0 = invite_form.find_element_by_id('id_form-0-email')
        submit = invite_form.find_element_by_id('submit_invite_friends')

    def test_email_field_necessary(self):
        # empty form
        self.selenium.get("{}{}".format(self.live_server_url, reverse('invite_users:invite_users')))
        invite_form = self.selenium.find_element_by_id('invite_friend_form')
        invite_form.find_element_by_id('submit_invite_friends').click()

        self.assertIn('Invite new User via email', self.selenium.page_source)
        self.assertIn('This field is required.', self.selenium.page_source)
        self.assertNotIn('Success', self.selenium.title)

        # only fill message => Failure
        self.selenium.get("{}{}".format(self.live_server_url, reverse('invite_users:invite_users')))
        invite_form = self.selenium.find_element_by_id('invite_friend_form')
        message = invite_form.find_element_by_id('id_additional_message')
        message.send_keys('I invite you!')
        invite_form.find_element_by_id('submit_invite_friends').click()

        self.assertIn('Invite new User via email', self.selenium.page_source)
        self.assertIn('This field is required.', self.selenium.page_source)
        self.assertNotIn('Success', self.selenium.title)

    def test_email_field_works(self):
        # fill message and email => Success
        self.selenium.get("{}{}".format(self.live_server_url, reverse('invite_users:invite_users')))
        invite_form = self.selenium.find_element_by_id('invite_friend_form')
        message = invite_form.find_element_by_id('id_additional_message')
        message.send_keys('I invite you!')
        email_send = 'b@b.com'
        invite_form.find_element_by_id('id_form-0-email').send_keys(email_send)
        submit = invite_form.find_element_by_id('submit_invite_friends').click()

        self.assertNotIn('Invite new User via email', self.selenium.page_source)
        self.assertNotIn('This field is required.', self.selenium.page_source)
        self.assertIn('Success', self.selenium.title, self.selenium.page_source)
        self.assertIn('You successfully invited:', self.selenium.page_source, self.selenium.page_source)
        self.assertIn(email_send, self.selenium.page_source, self.selenium.page_source)

        # fill only email => Success
        self.selenium.get("{}{}".format(self.live_server_url, reverse('invite_users:invite_users')))
        invite_form = self.selenium.find_element_by_id('invite_friend_form')
        email_send = 'b@b.com'
        invite_form.find_element_by_id('id_form-0-email').send_keys(email_send)
        submit = invite_form.find_element_by_id('submit_invite_friends').click()

        self.assertNotIn('Invite new User via email', self.selenium.page_source)
        self.assertNotIn('This field is required.', self.selenium.page_source)
        self.assertIn('Success', self.selenium.title, self.selenium.page_source)
        self.assertIn('You successfully invited:', self.selenium.page_source)
        self.assertIn(email_send, self.selenium.page_source)

    def test_invite_multiple(self):
        # add email and text, add additional users twice (without filling), invite => success
        # this is also a test for the clean method
        self.selenium.get("{}{}".format(self.live_server_url, reverse('invite_users:invite_users')))
        invite_form = self.selenium.find_element_by_id('invite_friend_form')
        m = 'I invite you!'
        e0 = 'a@a.com'
        e1 = 'b@b.com'
        e2 = 'c@c.com'
        e3 = 'd@d.com'
        error = 'You entered the same email twice. Each member can be invited only once'
        invite_form.find_element_by_id('id_additional_message').send_keys(m)
        invite_form.find_element_by_id('id_form-0-email').send_keys(e0)
        invite_form.find_element_by_id('submit_invite_more_friends').click()
        # add third field
        invite_form = self.selenium.find_element_by_id('invite_friend_form')
        invite_form.find_element_by_id('submit_invite_more_friends').click()
        # check filled stuff and invite
        invite_form = self.selenium.find_element_by_id('invite_friend_form')

        self.assertIn(m, invite_form.find_element_by_id('id_additional_message').text)
        invite_form.find_element_by_id('submit_invite_friends').click()

        self.assertIn('Success', self.selenium.title, self.selenium.page_source)
        self.assertIn('You successfully invited:', self.selenium.page_source)
        self.assertIn(e0, self.selenium.page_source)

        # add multiple emails with text => success
        self.selenium.get("{}{}".format(self.live_server_url, reverse('invite_users:invite_users')))
        self.selenium.find_element_by_id('invite_friend_form').find_element_by_id('submit_invite_more_friends').click()
        self.selenium.find_element_by_id('invite_friend_form').find_element_by_id('submit_invite_more_friends').click()
        self.selenium.find_element_by_id('invite_friend_form').find_element_by_id('submit_invite_more_friends').click()

        invite_form = self.selenium.find_element_by_id('invite_friend_form')
        invite_form.find_element_by_id('id_form-0-email').send_keys(e0)
        invite_form.find_element_by_id('id_form-1-email').send_keys(e1)
        invite_form.find_element_by_id('id_form-2-email').send_keys(e2)
        invite_form.find_element_by_id('id_form-3-email').send_keys(e3)
        invite_form.find_element_by_id('submit_invite_friends').click()

        self.assertIn('Success', self.selenium.title, self.selenium.page_source)
        self.assertIn('You successfully invited:', self.selenium.page_source)
        self.assertIn(e0, self.selenium.page_source)
        self.assertIn(e1, self.selenium.page_source)
        self.assertIn(e2, self.selenium.page_source)
        self.assertIn(e3, self.selenium.page_source)

        # add multiple emails with duplicated emails => failure
        self.selenium.get("{}{}".format(self.live_server_url, reverse('invite_users:invite_users')))
        self.selenium.find_element_by_id('invite_friend_form').find_element_by_id('submit_invite_more_friends').click()
        self.selenium.find_element_by_id('invite_friend_form').find_element_by_id('submit_invite_more_friends').click()

        invite_form = self.selenium.find_element_by_id('invite_friend_form')
        invite_form.find_element_by_id('id_form-0-email').send_keys(e0)
        invite_form.find_element_by_id('id_form-1-email').send_keys(e1)
        invite_form.find_element_by_id('id_form-2-email').send_keys(e0)
        invite_form.find_element_by_id('id_additional_message').send_keys(m)
        invite_form.find_element_by_id('submit_invite_friends').click()

        self.assertIn(error, self.selenium.page_source)
        # delete duplicated email and retry => success
        invite_form = self.selenium.find_element_by_id('invite_friend_form')
        self.assertIn(m, invite_form.find_element_by_id('id_additional_message').text)
        invite_form.find_element_by_id('id_form-2-email').clear()
        invite_form.find_element_by_id('submit_invite_friends').click()

        self.assertIn('Success', self.selenium.title, self.selenium.page_source)
        self.assertIn('You successfully invited:', self.selenium.page_source)
        self.assertIn(e0, self.selenium.page_source)
        self.assertIn(e1, self.selenium.page_source)

        # same as above, but with an additional 'invite more'
        self.selenium.get("{}{}".format(self.live_server_url, reverse('invite_users:invite_users')))
        self.selenium.find_element_by_id('invite_friend_form').find_element_by_id('submit_invite_more_friends').click()

        invite_form = self.selenium.find_element_by_id('invite_friend_form')
        invite_form.find_element_by_id('id_form-0-email').send_keys(e0)
        invite_form.find_element_by_id('id_form-1-email').send_keys(e0)
        invite_form.find_element_by_id('id_additional_message').send_keys(m)
        invite_form.find_element_by_id('submit_invite_friends').click()

        self.assertIn(error, self.selenium.page_source)
        self.selenium.find_element_by_id('invite_friend_form').find_element_by_id('submit_invite_more_friends').click()

        self.assertIn(error, self.selenium.page_source)
        # delete duplicated email and retry => success
        invite_form = self.selenium.find_element_by_id('invite_friend_form')
        self.assertIn(m, invite_form.find_element_by_id('id_additional_message').text)
        invite_form.find_element_by_id('id_form-1-email').clear()
        invite_form.find_element_by_id('submit_invite_friends').click()

        self.assertIn('Success', self.selenium.title, self.selenium.page_source)
        self.assertIn('You successfully invited:', self.selenium.page_source)
        self.assertIn(e0, self.selenium.page_source)

    @override_settings(EMAIL_BACKEND='django.core.mail.backends.filebased.EmailBackend')
    def test_send_email(self):
        # delete all previous stored emails to make testing easier
        try:
            dir_content = os.listdir(settings.EMAIL_FILE_PATH)
            if len(dir_content):
                print("\ndeleting {}/+{}".format(settings.EMAIL_FILE_PATH, dir_content))
                for f in dir_content:
                    file_path = os.path.join(settings.EMAIL_FILE_PATH, f)
                    os.remove(file_path)
        except Exception:
            pass

        self.selenium.get("{}{}".format(self.live_server_url, reverse('invite_users:invite_users')))
        self.selenium.find_element_by_id('invite_friend_form').find_element_by_id('submit_invite_more_friends').click()

        invite_form = self.selenium.find_element_by_id('invite_friend_form')
        m = 'Hey dude, this platform is awesome. U better check it out.'
        e0 = 'a@a.com'
        e1 = 'b@b.com'
        invite_form.find_element_by_id('id_additional_message').send_keys(m)
        invite_form.find_element_by_id('id_form-0-email').send_keys(e0)
        invite_form.find_element_by_id('id_form-1-email').send_keys(e1)
        invite_form.find_element_by_id('submit_invite_friends').click()

        self.assertIn('You successfully invited:', self.selenium.page_source)
        self.assertIn(e0, self.selenium.page_source)
        self.assertIn(e1, self.selenium.page_source)

        a = False
        b = False
        numberOfAdditionalMessages = 0
        # now verify those emails has been send
        dir_content = os.listdir(settings.EMAIL_FILE_PATH)
        self.assertEqual(len(dir_content), 1, "The email/s has/have not been send")
        for f in dir_content:
            file_path = os.path.join(settings.EMAIL_FILE_PATH, f)
            open_file = open(file_path)
            for line in open_file:
                if e0 in line:
                    a = True
                if e1 in line:
                    b = True
                if m in line:
                    numberOfAdditionalMessages += 1
            open_file.close()

        self.assertEqual(a, True, "email has not been send to {}".format(e0))
        self.assertEqual(b, True, "email has not been send to {}".format(e1))
        self.assertEqual(numberOfAdditionalMessages, 1,
                         "Email body has been corrupted. Additional message not included.")

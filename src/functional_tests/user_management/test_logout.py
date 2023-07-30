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
from lib.selenium_test_case import SeleniumTestCase
from selenium.webdriver.common.by import By
from django.urls import reverse

from django.contrib.auth import get_user_model

username = 'a'
pw = 'a1111111'


class LogoutTest(SeleniumTestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username, 'a@b.com', pw)

    def test_reachable(self):
        self.selenium.get("{}{}".format(self.live_server_url, reverse('logout')))
        self.assertNotIn('Not Found', self.selenium.page_source)
        self.assertIn('Login', self.selenium.title)

    def test_logout_after_login(self):
        self.selenium.get("{}{}".format(self.live_server_url, reverse('login')))
        login_form = self.selenium.find_element(By.ID, 'id_login_form')
        login_form.find_element(By.ID, 'id_username').send_keys(username)
        login_form.find_element(By.ID, 'id_password').send_keys(pw)
        login_form.find_element(By.ID, 'id_submit_login').click()

        self.selenium.get("{}{}".format(self.live_server_url, reverse('logout')))
        self.assertIn('You have been successfully logged out.', self.selenium.page_source)

    def test_logout_without_login(self):
        self.selenium.get("{}{}".format(self.live_server_url, reverse('logout')))
        self.assertNotIn('You have been successfully logged out.', self.selenium.page_source)

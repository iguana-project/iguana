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
from django.test import Client
from lib.selenium_test_case import SeleniumTestCase
from selenium.webdriver.common.by import By
from django.urls import reverse

from project.models import Project
from issue.models import Issue
from django.contrib.auth import get_user_model


class OleaTest(SeleniumTestCase):

    def setUp(self):
        self.user = get_user_model().objects.create_user('a', 'b', 'c')
        self.project = Project(creator=self.user, name="Blubber-Project", name_short="BRP")
        self.project.save()
        self.project.developer.add(self.user)
        self.project.manager.add(self.user)
        # Uses the cookie hack from:
        # https://stackoverflow.com/questions/22494583/login-with-code-when-using-liveservertestcase-with-django
        client = Client()
        client.login(username='a', password='c')
        self.cookie = client.cookies['sessionid']
        self.selenium.get("{}{}".format(self.live_server_url, reverse('invite_users:invite_users')))
        self.selenium.add_cookie({'name': 'sessionid', 'value': self.cookie.value, 'secure': False, 'path': '/'})
        self.selenium.refresh()

    def test_oleainput(self):
        driver = self.selenium
        driver.get('{}{}'.format(self.live_server_url,
                                 reverse('sprint:sprintboard', kwargs={'project': self.project.name_short})))

        driver.find_element(By.ID, "expression").send_keys("Test-Issue :Task")
        driver.find_element(By.ID, "expression").submit()
        self.assertEqual("Test-Issue", driver.find_element(By.CSS_SELECTOR, "#issue_title_1").text)
        driver.find_element(By.ID, "expression").clear()
        driver.find_element(By.ID, "expression").send_keys("Another issue :Bug")
        driver.find_element(By.ID, "expression").submit()
        self.assertEqual("Another issue", driver.find_element(By.CSS_SELECTOR, "#issue_title_2").text)
        self.assertEqual("Bug", driver.find_element(By.CSS_SELECTOR, "#issue_type_2").text)
        driver.find_element(By.ID, "expression").clear()
        driver.find_element(By.ID, "expression").send_keys(">BRP-2 :Task")
        driver.find_element(By.ID, "expression").submit()
        self.assertEqual("Task", driver.find_element(By.CSS_SELECTOR, "#issue_type_2").text)

        # go to backlog and try olea there too
        driver.find_element(By.LINK_TEXT, "Backlog").click()
        driver.find_element(By.ID, "expression").send_keys("And another one :Bug")
        driver.find_element(By.ID, "expression").submit()
        self.assertIn("BRP-3\nAnd another one", driver.find_element(By.ID, "backlog_issue_3").text)

        # verify that all issues are assigned to given project and no more issues were created
        self.project.refresh_from_db()
        self.assertEqual(self.project.issue.count(), 3)
        self.assertEqual(Issue.objects.count(), 3)

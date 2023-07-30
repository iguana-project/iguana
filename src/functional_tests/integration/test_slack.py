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
import time
from lib.selenium_test_case import SeleniumTestCase
from selenium.webdriver.common.by import By
from django.urls import reverse

from unittest.mock import patch

from django.contrib.auth import get_user_model
from project.models import Project
from integration.models import SlackIntegration
from issue.models import Issue
from selenium.webdriver.common.keys import Keys

try:
    from common.settings import SLACK_SECRET, SLACK_VERIFICATION, SLACK_ID, HOST
except ImportError:
    SLACK_ID = None


class SlackTest(SeleniumTestCase):
    def setUp(self):
        # Uses the cookie hack from:
        # https://stackoverflow.com/questions/22494583/login-with-code-when-using-liveservertestcase-with-django
        client = Client()
        self.user = get_user_model().objects.create_user('a', 'b', 'c')
        client.login(username='a', password='c')
        self.cookie = client.cookies['sessionid']
        self.selenium.get("{}{}".format(self.live_server_url, "/"))
        self.selenium.add_cookie({'name': 'sessionid', 'value': self.cookie.value, 'secure': False, 'path': '/'})
        self.selenium.refresh()

        self.short = "asdf"
        self.project = Project(creator=self.user, name="long_asdf", name_short=self.short)
        self.project.save()
        self.project.developer.set((self.user.pk,))
        self.project.manager.set((self.user.pk,))
        self.project.save()

        si = SlackIntegration()
        si.project = self.project
        si.api_token = "foo"
        si.channel = "channel"
        si.save()

        self.title_name = 'This is title'
        self.comment = "This is comment"

    @patch('integration.models.SlackIntegration.slack')
    def test_issue_create(self, slackmock):
        self.selenium.get('{}{}'.format(self.live_server_url, reverse('issue:create',
                                        kwargs={'project': self.short})))
        f = self.selenium.find_element(By.ID, 'id_title')
        f.send_keys(self.title_name)
        self.selenium.find_element(By.ID, 'id_submit_create').click()
        slackmock.chat_postMessage.assert_called_with(
            channel="channel",
            attachments=[{
                'fallback': str(self.user) + " created issue "+self.short+"-1 "+self.title_name+".",
                'pretext': 'New Issue:',
                'text': "",
                'title': self.short+"-1 "+self.title_name,
                'title_link': "http://localhost:8000/project/"+self.short+"/issue/1/",
                'author_name': str(self.user),
                'author_link': "http://localhost:8000" + self.user.get_absolute_url(),
                'author_icon': "http://localhost:8000" + self.user.avatar.url,
                'color': 'good',
            }]
        )

    @patch('integration.models.SlackIntegration.slack')
    def test_issue_modify(self, slackmock):
        issue = Issue()
        issue.title = self.title_name
        issue.project = self.project
        issue.save()

        self.selenium.get(
                '{}{}'.format(
                    self.live_server_url,
                    reverse('issue:edit', kwargs={'project': self.short, 'sqn_i': issue.number})
                    )
                )

        # open assignee autocomplete field
        self.selenium.find_element(By.CSS_SELECTOR, "input.select2-search__field").click()
        # select first result
        self.selenium.find_elements(By.CSS_SELECTOR, '#select2-id_assignee-results li')[0].click()
        # close autocomplete
        self.selenium.find_element(By.CSS_SELECTOR, "input.select2-search__field").send_keys(Keys.ESCAPE)

        self.selenium.find_element(By.ID, 'id_submit_edit').click()
        slackmock.chat_postMessage.assert_called_with(
            channel="channel",
            attachments=[{
                'fallback': str(self.user) + " changed issue "+self.short+"-1 "+self.title_name+".",
                'pretext': 'Issue changed:',
                'title': self.short+"-1 "+self.title_name,
                'title_link': "http://localhost:8000/project/"+self.short+"/issue/1/",
                'author_name': str(self.user),
                'author_link': "http://localhost:8000" + self.user.get_absolute_url(),
                'author_icon': "http://localhost:8000" + self.user.avatar.url,
                'fields': [{
                    'title': 'Assignee',
                    'value': ' → a',
                    'short': True,
                    }],
                'color': 'good',
            }]
        )

    @patch('integration.models.SlackIntegration.slack')
    def test_comment(self, slackmock):
        issue = Issue()
        issue.title = self.title_name
        issue.project = self.project
        issue.save()

        self.selenium.get(
                '{}{}'.format(
                    self.live_server_url,
                    reverse('issue:detail', kwargs={'project': self.project.name_short, 'sqn_i': issue.number})
                    )
                )
        f = self.selenium.find_element(By.ID, "wmd-input-id_text")
        f.send_keys(self.comment)
        self.selenium.find_element(By.NAME, "action").click()
        slackmock.chat_postMessage.assert_called_with(
            channel="channel",
            attachments=[{
                'fallback': str(self.user) + ' commented on \"'+self.short+'-1 '+self.title_name+'\".',
                'pretext': 'New comment:',
                'text': self.comment,
                'title': self.short+"-1 "+self.title_name,
                'title_link': "http://localhost:8000/project/"+self.short+"/issue/1/",
                'author_name': str(self.user),
                'author_link': "http://localhost:8000" + self.user.get_absolute_url(),
                'author_icon': "http://localhost:8000" + self.user.avatar.url,
                'color': 'good',
            }]
        )

    # TODO TESTCASE for olea-bar

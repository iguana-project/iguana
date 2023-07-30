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

import os
import tempfile
import datetime

from django.contrib.auth import get_user_model
from project.models import Project
from issue.models import Issue
from kanbancol.models import KanbanColumn

from common.settings import MEDIA_ROOT


class AttachmentTest(SeleniumTestCase):

    def setUp(self):
        self.user = get_user_model().objects.create_user('a_user', 'a@a.com', 'a1234568')
        self.project = Project(name="Projectname", name_short="PRN", creator=self.user)
        self.project.save()
        self.project.manager.add(self.user)
        # Uses the cookie hack from:
        # https://stackoverflow.com/questions/22494583/login-with-code-when-using-liveservertestcase-with-django
        client = Client()
        client.login(username='a_user', password='a1234568')
        self.cookie = client.cookies['sessionid']
        self.selenium.get("{}{}".format(self.live_server_url, reverse('invite_users:invite_users')))
        self.selenium.add_cookie({'name': 'sessionid', 'value': self.cookie.value, 'secure': False, 'path': '/'})
        self.selenium.refresh()

    def test_reachable_and_elements_exist(self):
        # TODO TESTCASE verify that the page is available + check (some) content like the title + check existence
        #               of forms and their form elements by their ids!
        pass

    def test_upload_attachment(self):
        # TODO TESTCASE upload file as an attachment
        # TODO TESTCASE upload file together with a comment
        driver = self.selenium

        # create attachment file
        filecontent1 = 'Hello World File 1'
        temp1 = tempfile.NamedTemporaryFile(delete=False)
        temp1.write(filecontent1.encode())
        temp1.close()

        # create issue and attach file
        issue = Issue(title="title", kanbancol=KanbanColumn.objects.get(project=self.project, name="Todo"),
                      due_date=str(datetime.date.today()), priority=3, storypoints=2, description="blubber",
                      project=self.project
                      )
        issue.save()

        driver.get("{}{}".format(self.live_server_url, reverse('issue:detail',
                                 kwargs={'project': self.project.name_short, 'sqn_i': issue.number})))

        driver.find_element(By.CSS_SELECTOR,
                            "#attachment-form > div.form-group > div.row.bootstrap3-multi-input > \
                            div.col-xs-12 > #id_file"
                            ).clear()
        driver.find_element(By.CSS_SELECTOR,
                            "#attachment-form > div.form-group > div.row.bootstrap3-multi-input > \
                            div.col-xs-12 > #id_file"
                            ).send_keys(temp1.name)
        driver.find_element(By.ID, "attachment-btn").click()

        # assert that attached file exists
        self.assertIn(driver.find_element(By.ID, "issue_detail_attach_get_1").text, temp1.name)
        self.assertEqual(issue.attachments.count(), 1)
        attachment = issue.attachments.first()
        self.assertIn(filecontent1, attachment.file.read().decode())
        attachment.file.close()

        # delete the uploaded file from the server
        os.unlink(MEDIA_ROOT + '/' + attachment.file.name)
        # delete the uploaded file locally
        os.unlink(temp1.name)

    def test_required_fields(self):
        driver = self.selenium

        # create issue and attach file
        issue = Issue(title="title", kanbancol=KanbanColumn.objects.get(project=self.project, name="Todo"),
                      due_date=str(datetime.date.today()), priority=3, storypoints=2, description="blubber",
                      project=self.project
                      )
        issue.save()

        driver.get("{}{}".format(self.live_server_url, reverse('issue:detail',
                                 kwargs={'project': self.project.name_short, 'sqn_i': issue.number})))
        driver.find_element(By.ID, "attachment-btn").click()

        # assert that no attachment is created
        self.assertEqual(issue.attachments.count(), 0)

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

from django.contrib.auth import get_user_model
from project.models import Project
from selenium.webdriver.common.keys import Keys


# TODO we might wanna test the href-links on those pages
class ProjectTest(SeleniumTestCase):

    def setUp(self):
        self.user = get_user_model().objects.create_user('test', 'test@test.com', 'test')
        self.user2 = get_user_model().objects.create_user('new_user', 'test@test2.com', 'test')
        # Uses the cookie hack from:
        # https://stackoverflow.com/questions/22494583/login-with-code-when-using-liveservertestcase-with-django
        client = Client()
        client.login(username='test', password='test')
        self.cookie = client.cookies['sessionid']
        self.selenium.get("{}{}".format(self.live_server_url, reverse('project:create')))
        self.selenium.add_cookie({'name': 'sessionid', 'value': self.cookie.value, 'secure': False, 'path': '/'})
        self.selenium.refresh()

    def test_reachable_and_elements_exist(self):
        # TODO TESTCASE
        # TODO for each site check it is available + check (some) content like the title + check existence of forms
        #      and their form elements!
        # TODO project:list
        # TODO project:create - check form and elements by id
        # TODO project:detail
        # TODO project:edit - check form and elements by id
        # TODO project:delete
        pass

    def test_fields_are_required(self):
        # TODO TESTCASE
        # TODO check required-fields for the following
        #     TODO project:create - Name, short name
        #     TODO project:edit - Name
        pass

    def test_fields_are_unique(self):
        # TODO TESTCASE
        # TODO project:create - name, short name
        # TODO project:edit - name
        pass

    def test_further_error_messages(self):
        # TODO TESTCASE
        pass

    def test_create_project(self):
        self.selenium.get('{}{}'.format(self.live_server_url, reverse('project:create')))
        create_form = self.selenium.find_element(By.ID, "id_create_form")
        name = 'TestProjekt'
        create_form.find_element(By.ID, "id_name").send_keys(name)
        create_form.find_element(By.ID, "id_name_short").send_keys('TP')
        create_form.find_element(By.ID, "id_description").send_keys('This is a description for our TestProject')
        create_form.find_element(By.CSS_SELECTOR, 'input.select2-search__field').send_keys('te')
        # TODO TESTCASE this doesn't work on the create form - y doesn't this work?
        self.selenium.find_element(By.CSS_SELECTOR,
                                   'li.select2-results__option.select2-results__option--highlighted'
                                   ).click()
        create_form.find_element(By.CSS_SELECTOR, "input.select2-search__field").send_keys(Keys.ESCAPE)
        create_form.find_element(By.ID, 'id_submit_create').click()
        self.assertEqual(self.selenium.title, name)

    def test_edit_project(self):
        project = Project(name='TestProject', name_short='TP',
                          description='This is a descprition for our TestProject', creator=self.user)
        project.save()
        project.manager.add(self.user)

        self.selenium.get("{}{}".format(self.live_server_url, reverse('project:edit',
                                                                      kwargs={'project': project.name_short})))
        edit_form = self.selenium.find_element(By.ID, "id_edit_form")
        edit_form.find_element(By.ID, "id_name").send_keys('Renamed')
        edit_form.find_element(By.ID, 'id_submit_edit').click()
        self.assertEqual(self.selenium.title, 'TestProjectRenamed')

    def test_warning_at_delete(self):
        # TODO TESTCASE
        pass

    def test_delete_project(self):
        # TODO TESTCASE
        pass

    def test_keep_and_dont_delete_project(self):
        # TODO TESTCASE
        pass

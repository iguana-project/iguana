"""
Iguana (c) by Marc Ammon, Moritz Fickenscher, Lukas Fridolin,
Michael Gunselmann, Katrin Raab, Christian Strate

Iguana is licensed under a
Creative Commons Attribution-ShareAlike 4.0 International License.

You should have received a copy of the license along with this
work. If not, see <http://creativecommons.org/licenses/by-sa/4.0/>.
"""
from django.test import Client
from lib.selenium_test_case import SeleniumTestCase
from django.urls import reverse

from django.contrib.auth import get_user_model
from project.models import Project


class KanbancolTest(SeleniumTestCase):
    def setUp(self):
        # Uses the cookie hack from:
        # https://stackoverflow.com/questions/22494583/login-with-code-when-using-liveservertestcase-with-django
        client = Client()
        user = get_user_model().objects.create_user('a', 'b', 'c')
        client.login(username='a', password='c')
        self.cookie = client.cookies['sessionid']

        self.short = "asdf"
        self.project = Project(creator=user, name="asdf", name_short=self.short)
        self.project.save()
        self.project.developer.set((user.pk,))
        self.project.manager.set((user.pk,))
        self.project.save()

    def test_create(self):
        self.selenium.get('{}{}'.format(self.live_server_url, reverse('kanbancol:create',
                                        kwargs={'project': self.short})))
        self.selenium.add_cookie({'name': 'sessionid', 'value': self.cookie.value, 'secure': False, 'path': '/'})
        self.selenium.refresh()
        self.selenium.get('{}{}'.format(self.live_server_url, reverse('kanbancol:create',
                                        kwargs={'project': self.short})))
        field = self.selenium.find_element_by_name("name")
        field.send_keys('Palimpalim')
        self.selenium.find_element_by_css_selector('.save').click()
        self.assertEqual(self.selenium.title, 'Edit asdf')

    def test_delete_column_and_test_in_project_edit(self):
        # TODO TESTCASE
        pass

    def test_create_column_and_test_in_project_edit(self):
        # TODO TESTCASE
        pass

    def test_move_column_up_in_project_edit(self):
        # TODO TESTCASE
        pass

    def test_change_number_of_columns_and_test(self):
        # TODO TESTCASE
        # TODO create some
        # TODO delete some of the first ones
        # TODO verify everything works as expected
        pass

    def test_delete_todo_column_and_stop_running_sprint(self):
        # TODO TESTCASE
        # TODO what happens with those issues?
        pass

"""
Iguana (c) by Marc Ammon, Moritz Fickenscher, Lukas Fridolin,
Michael Gunselmann, Katrin Raab, Christian Strate

Iguana is licensed under a
Creative Commons Attribution-ShareAlike 4.0 International License.

You should have received a copy of the license along with this
work. If not, see <http://creativecommons.org/licenses/by-sa/4.0/>.
"""
import time
from django.test import Client
from lib.selenium_test_case import SeleniumTestCase
from django.urls import reverse

from django.contrib.auth import get_user_model
from project.models import Project
from tag.models import Tag
from issue.models import Issue


class FilterTest(SeleniumTestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user('a_user', 'a@a.com', 'a1234568')
        self.project = Project(name="Projectname", name_short="proj", creator=self.user)
        self.project.save()
        self.project.manager.add(self.user)
        self.short = self.project.name_short

        tag = Tag(project=self.project, tag_text="foo")
        tag.save()
        Issue(project=self.project, title="a").save()
        issue = Issue(project=self.project, title="b")
        issue.save()
        issue.tags.add(tag)

        # Uses the cookie hack from:
        # https://stackoverflow.com/questions/22494583/login-with-code-when-using-liveservertestcase-with-django
        client = Client()
        client.login(username='a_user', password='a1234568')
        self.cookie = client.cookies['sessionid']
        self.selenium.get("{}{}".format(self.live_server_url, reverse('invite_users:invite_users')))
        self.selenium.add_cookie({'name': 'sessionid', 'value': self.cookie.value, 'secure': False, 'path': '/'})
        self.selenium.refresh()

    def test_filter_title(self):
        response = self.selenium.get(self.live_server_url + reverse('backlog:backlog', kwargs={'project': self.short}))
        elements = self.selenium.find_elements_by_class_name("backlog-issue")
        self.assertTrue(elements[0].is_displayed())
        self.assertTrue(elements[1].is_displayed())

        filter_box = self.selenium.find_element_by_id("text-filter")
        filter_box.send_keys("a")
        self.assertTrue(elements[0].is_displayed())
        self.assertFalse(elements[1].is_displayed())

    def test_filter_number(self):
        response = self.selenium.get(self.live_server_url + reverse('backlog:backlog', kwargs={'project': self.short}))
        elements = self.selenium.find_elements_by_class_name("backlog-issue")
        self.assertTrue(elements[0].is_displayed())
        self.assertTrue(elements[1].is_displayed())

        filter_box = self.selenium.find_element_by_id("text-filter")
        filter_box.send_keys("1")
        self.assertTrue(elements[0].is_displayed())
        self.assertFalse(elements[1].is_displayed())

    def test_filter_tag(self):
        response = self.selenium.get(self.live_server_url + reverse('backlog:backlog', kwargs={'project': self.short}))
        elements = self.selenium.find_elements_by_class_name("backlog-issue")
        self.assertTrue(elements[0].is_displayed())
        self.assertTrue(elements[1].is_displayed())

        filter_box = self.selenium.find_element_by_id("text-filter")
        filter_box.send_keys("fo")
        self.assertFalse(elements[0].is_displayed())
        self.assertTrue(elements[1].is_displayed())

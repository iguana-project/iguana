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
import re

from django.contrib.auth import get_user_model
from project.models import Project
from tag.models import Tag


class TagTest(StaticSeleniumTestCase):
    p0_name = 'proj0'
    p0_short = 'sho0'

    def setUp(self):
        self.user = get_user_model().objects.create_user('a_user', 'a@a.com', 'a1234568')
        self.project0 = Project(name=self.p0_name, name_short=self.p0_short, creator=self.user)
        self.project0.save()
        self.project0.manager.add(self.user)
        self.project0.save()

        # Uses the cookie hack from:
        # https://stackoverflow.com/questions/22494583/login-with-code-when-using-liveservertestcase-with-django
        client = Client()
        client.login(username='a_user', password='a1234568')
        self.cookie = client.cookies['sessionid']
        self.selenium.get("{}{}".format(self.live_server_url, reverse('invite_users:invite_users')))
        self.selenium.add_cookie({'name': 'sessionid', 'value': self.cookie.value, 'secure': False, 'path': '/'})
        self.selenium.refresh()

    def test_reachable_and_elements_exist(self):
        self.selenium.get("{}{}".format(self.live_server_url, reverse('tag:tag', kwargs={'project': self.p0_short})))
        self.assertNotIn('Not Found', self.selenium.page_source)
        self.assertIn('Manage Tags', self.selenium.title)
        # delete_form and list of tags aren't present anymore, if there are no tags yet created
        self.assertNotIn('<ul class="list-group>', self.selenium.page_source)
        create_form = self.selenium.find_element_by_id('id_create-tags')

        create_form.find_element_by_id('id_tag_text')
        create_form.find_element_by_id('id_submit_create_tag')

    def test_tag_name_required(self):
        self.selenium.get("{}{}".format(self.live_server_url, reverse('tag:tag', kwargs={'project': self.p0_short})))
        create_form = self.selenium.find_element_by_id('id_create-tags')
        self.assertTrue(create_form.find_element_by_id('id_tag_text').get_attribute('required'))

    def test_tags_are_unique_per_project(self):
        tag = "please_dont_duplicate_me"
        self.selenium.get("{}{}".format(self.live_server_url, reverse('tag:tag', kwargs={'project': self.p0_short})))
        create_form = self.selenium.find_element_by_id('id_create-tags')
        create_form.find_element_by_id('id_tag_text').send_keys(tag)
        create_form.find_element_by_id('id_submit_create_tag').click()
        create_form = self.selenium.find_element_by_id('id_create-tags')
        create_form.find_element_by_id('id_tag_text').send_keys(tag)
        create_form.find_element_by_id('id_submit_create_tag').click()
        # expect error message
        self.assertIn('There is already a Tag' + ' "{}" '.format(tag) + 'for this project and you are only ' +
                      'allowed to have it once per project.', self.selenium.page_source)
        # expect tag only be shown once! we search for the checkbox
        # because we use the tag name itself more often in the template
        self.assertEqual(len(re.findall("tag_checkbox_"+tag, self.selenium.page_source)), 1)

    def test_create_and_delete_tags(self):
        self.selenium.get("{}{}".format(self.live_server_url, reverse('tag:tag', kwargs={'project': self.p0_short})))
        tag0 = 'tag0_project0'
        tag1 = 'tag1_project0'
        tag2 = 'tag2_project0'
        tag3 = 'tag3_project0'
        # create tags
        create_form = self.selenium.find_element_by_id('id_create-tags')
        create_form.find_element_by_id('id_tag_text').send_keys(tag0)
        create_form.find_element_by_id('id_color').send_keys('286090')
        create_form.find_element_by_id('id_submit_create_tag').click()
        self.assertIn(tag0, self.selenium.page_source)

        create_form = self.selenium.find_element_by_id('id_create-tags')
        create_form.find_element_by_id('id_tag_text').send_keys(tag1)
        create_form.find_element_by_id('id_color').send_keys('fbec5d')
        create_form.find_element_by_id('id_submit_create_tag').click()
        self.assertIn(tag0, self.selenium.page_source)
        self.assertIn(tag1, self.selenium.page_source)

        create_form = self.selenium.find_element_by_id('id_create-tags')
        create_form.find_element_by_id('id_tag_text').send_keys(tag2)
        create_form.find_element_by_id('id_color').send_keys('a94442')
        create_form.find_element_by_id('id_submit_create_tag').click()
        self.assertIn(tag0, self.selenium.page_source)
        self.assertIn(tag1, self.selenium.page_source)
        self.assertIn(tag2, self.selenium.page_source)

        # delete tag0
        delete_form = self.selenium.find_element_by_id('id_delete-tags')
        delete_form.find_element_by_id('id_tag_checkbox_'+tag0).click()
        delete_form.find_element_by_id('id_submit_delete_tags').click()
        self.assertNotIn(tag0, self.selenium.page_source)
        self.assertIn(tag1, self.selenium.page_source)
        self.assertIn(tag2, self.selenium.page_source)

        # delete tag2
        delete_form = self.selenium.find_element_by_id('id_delete-tags')
        delete_form.find_element_by_id('id_tag_checkbox_'+tag2).click()
        delete_form.find_element_by_id('id_submit_delete_tags').click()
        self.assertNotIn(tag0, self.selenium.page_source)
        self.assertIn(tag1, self.selenium.page_source)
        self.assertNotIn(tag2, self.selenium.page_source)

        # create tag3
        create_form = self.selenium.find_element_by_id('id_create-tags')
        create_form.find_element_by_id('id_tag_text').send_keys(tag3)
        create_form.find_element_by_id('id_color').send_keys('286090')
        create_form.find_element_by_id('id_submit_create_tag').click()
        self.assertNotIn(tag0, self.selenium.page_source)
        self.assertIn(tag1, self.selenium.page_source)
        self.assertNotIn(tag2, self.selenium.page_source)
        self.assertIn(tag3, self.selenium.page_source)

        # delete tag1
        delete_form = self.selenium.find_element_by_id('id_delete-tags')
        delete_form.find_element_by_id('id_tag_checkbox_'+tag1).click()
        delete_form.find_element_by_id('id_submit_delete_tags').click()
        self.assertNotIn(tag0, self.selenium.page_source)
        self.assertNotIn(tag1, self.selenium.page_source)
        self.assertNotIn(tag2, self.selenium.page_source)
        self.assertIn(tag3, self.selenium.page_source)

    def test_delete_multiple_tags(self):
        self.selenium.get("{}{}".format(self.live_server_url, reverse('tag:tag', kwargs={'project': self.p0_short})))
        tag0 = 'tag0_project0'
        tag1 = 'tag1_project0'
        tag2 = 'tag2_project0'
        tag3 = 'tag3_project0'
        tag4 = 'tag4_project0'
        create_form = self.selenium.find_element_by_id('id_create-tags')
        create_form.find_element_by_id('id_tag_text').send_keys(tag0)
        create_form.find_element_by_id('id_submit_create_tag').click()
        create_form = self.selenium.find_element_by_id('id_create-tags')
        create_form.find_element_by_id('id_tag_text').send_keys(tag1)
        create_form.find_element_by_id('id_submit_create_tag').click()
        create_form = self.selenium.find_element_by_id('id_create-tags')
        create_form.find_element_by_id('id_tag_text').send_keys(tag2)
        create_form.find_element_by_id('id_submit_create_tag').click()
        create_form = self.selenium.find_element_by_id('id_create-tags')
        create_form.find_element_by_id('id_tag_text').send_keys(tag3)
        create_form.find_element_by_id('id_submit_create_tag').click()
        create_form = self.selenium.find_element_by_id('id_create-tags')
        create_form.find_element_by_id('id_tag_text').send_keys(tag4)
        create_form.find_element_by_id('id_submit_create_tag').click()
        self.assertIn(tag0, self.selenium.page_source)
        self.assertIn(tag1, self.selenium.page_source)
        self.assertIn(tag2, self.selenium.page_source)
        self.assertIn(tag3, self.selenium.page_source)
        self.assertIn(tag4, self.selenium.page_source)

        delete_form = self.selenium.find_element_by_id('id_delete-tags')
        delete_form.find_element_by_id('id_tag_checkbox_'+tag0).click()
        delete_form.find_element_by_id('id_tag_checkbox_'+tag3).click()
        delete_form.find_element_by_id('id_tag_checkbox_'+tag1).click()
        delete_form.find_element_by_id('id_submit_delete_tags').click()
        self.assertNotIn(tag0, self.selenium.page_source)
        self.assertNotIn(tag1, self.selenium.page_source)
        self.assertIn(tag2, self.selenium.page_source)
        self.assertNotIn(tag3, self.selenium.page_source)
        self.assertIn(tag4, self.selenium.page_source)

    def test_delete_all(self):
        tags = ['tag0_project0', 'tag0_project1', 'tag0_project2', 'tag0_project3']
        tag0 = Tag(tag_text=tags[0], project=self.project0, color="ef2929")
        tag1 = Tag(tag_text=tags[1], project=self.project0, color="ef2929")
        tag2 = Tag(tag_text=tags[2], project=self.project0, color="ef2929")
        tag3 = Tag(tag_text=tags[3], project=self.project0, color="ef2929")
        tag0.save()
        tag1.save()
        tag2.save()
        tag3.save()
        self.selenium.get("{}{}".format(self.live_server_url, reverse('tag:tag', kwargs={'project': self.p0_short})))
        self.selenium.find_element_by_id('id_select_all').click()
        self.selenium.find_element_by_id('id_delete-tags').find_element_by_id('id_submit_delete_tags').click()
        for tag in tags:
            self.assertNotIn(tag, self.selenium.page_source)

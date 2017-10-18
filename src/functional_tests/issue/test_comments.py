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
import tempfile
import datetime

from django.contrib.auth import get_user_model
from project.models import Project
from kanbancol.models import KanbanColumn
from issue.models import Issue


class CommentsTest(StaticSeleniumTestCase):

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
        driver = self.selenium

        # create attachment file
        filecontent1 = 'Hello World File 1'
        temp1 = tempfile.NamedTemporaryFile(delete=False)
        temp1.write(filecontent1.encode())
        temp1.close()

        issue = Issue(title="title", kanbancol=KanbanColumn.objects.get(project=self.project, name="Todo"),
                      due_date=str(datetime.date.today()), priority=3, storypoints=2, description="blubber",
                      project=self.project
                      )
        issue.save()

        driver.get("{}{}".format(self.live_server_url, reverse('issue:detail',
                                 kwargs={'project': self.project.name_short, 'sqn_i': issue.number})))

        # add comment
        driver.find_element_by_id("id_text").clear()
        driver.find_element_by_id("id_text").send_keys("test-comment")
        driver.find_element_by_name("action").click()

        # add another comment with attachment
        driver.find_element_by_id("id_text").clear()
        driver.find_element_by_id("id_text").send_keys("another comment")
        driver.find_element_by_id("id_file").clear()
        driver.find_element_by_id("id_file").send_keys(temp1.name)
        driver.find_element_by_name("action").click()

        # check count of db objects
        self.assertEqual(issue.attachments.count(), 1)
        self.assertEqual(issue.comments.count(), 2)

        # assert that comments are present
        self.assertEqual("test-comment",
                         driver.find_element_by_css_selector("div.comment-content > p").text
                         )
        self.assertEqual("another comment",
                         driver.find_element_by_css_selector("#comment2 > div.comment-content > p").text
                         )
        self.assertIn("Attached file: ", driver.find_element_by_css_selector("div.comment-footer").text)
        self.assertIn(driver.find_element_by_css_selector("div.comment-footer").text.split(": ")[1], temp1.name)

        # assert that attached file is present in attachments list
        self.assertIn(driver.find_element_by_id("issue_detail_attach_get_1").text, temp1.name)

        # edit comment
        driver.find_element_by_id("issue_detail_comment_edit_1").click()
        driver.find_element_by_id("id_text").clear()
        driver.find_element_by_id("id_text").send_keys("text-comment")
        driver.find_element_by_id("comment-btn").click()

        # assert that text was saved
        self.assertEqual("text-comment", driver.find_element_by_css_selector("div.comment-content > p").text)
        self.assertEqual("last modified 0 minutes ago", driver.find_element_by_css_selector("em").text)

        # delete comment and check
        driver.find_element_by_id("issue_detail_comment_delete_1").click()
        self.assertEqual(issue.comments.count(), 1)
        self.assertEqual("another comment", driver.find_element_by_css_selector("div.comment-content > p").text)

        # delete second comment and check that attachment is still present
        driver.find_element_by_id("issue_detail_comment_delete_1").click()
        self.assertIn(driver.find_element_by_id("issue_detail_attach_get_1").text, temp1.name)
        self.assertEqual(issue.comments.count(), 0)
        self.assertEqual(issue.attachments.count(), 1)

        # clean up
        os.remove(temp1.name)

    def test_required_field_in_edit(self):
        driver = self.selenium

        # create issue
        issue = Issue(title="title", kanbancol=KanbanColumn.objects.get(project=self.project, name="Todo"),
                      due_date=str(datetime.date.today()), priority=3, storypoints=2, description="blubber",
                      project=self.project
                      )
        issue.save()

        driver.get("{}{}".format(self.live_server_url, reverse('issue:detail',
                                 kwargs={'project': self.project.name_short, 'sqn_i': issue.number})))

        # add comment
        driver.find_element_by_id("id_text").clear()
        driver.find_element_by_id("id_text").send_keys("test-comment")
        driver.find_element_by_name("action").click()

        # edit comment with empty text field => should fail
        driver.find_element_by_id("issue_detail_comment_edit_1").click()
        driver.find_element_by_id("id_text").clear()
        driver.find_element_by_id("comment-btn").click()
        self.assertIn("Edit comment", driver.page_source)
        self.assertEqual(issue.comments.first().text, "test-comment")
        self.assertEqual(issue.comments.count(), 1)

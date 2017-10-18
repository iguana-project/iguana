"""
Iguana (c) by Marc Ammon, Moritz Fickenscher, Lukas Fridolin,
Michael Gunselmann, Katrin Raab, Christian Strate

Iguana is licensed under a
Creative Commons Attribution-ShareAlike 4.0 International License.

You should have received a copy of the license along with this
work. If not, see <http://creativecommons.org/licenses/by-sa/4.0/>.
"""
from django.test import Client
import time
from lib.selenium_test_case import StaticSeleniumTestCase
from django.urls import reverse

from unittest.mock import patch

from django.contrib.auth import get_user_model
from project.models import Project
from integration.models import SlackIntegration
from issue.models import Issue

try:
    from common.settings import SLACK_SECRET, SLACK_VERIFICATION, SLACK_ID, HOST
except:
    SLACK_ID = None


class SlackTest(StaticSeleniumTestCase):
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
        self.project = Project(creator=self.user, name="asdf", name_short=self.short)
        self.project.save()
        self.project.developer.set((self.user.pk,))
        self.project.manager.set((self.user.pk,))
        self.project.save()

        si = SlackIntegration()
        si.project = self.project
        si.api_token = "foo"
        si.channel = "channel"
        si.save()

    @patch('integration.models.SlackClient')
    def test_issue_create(self, slackmock):
        # TODO TESTCASE broken test
        return
        self.selenium.get('{}{}'.format(self.live_server_url, reverse('issue:create',
                                        kwargs={'project': self.short})))
        f = self.selenium.find_element_by_id('id_title')
        f.send_keys('This is title')
        self.selenium.find_element_by_id('id_submit_create').click()
        slackmock().api_call.assert_called_with(
            "chat.postMessage",
            channel="channel",
            attachments=[{
                'fallback': str(self.user) + " created issue asdf-1 This is title.",
                'pretext': 'New Issue:',
                'text': "",
                'title': "asdf-1 This is title",
                'title_link': "http://localhost:8000/project/asdf/issue/1/",
                'author_name': str(self.user),
                'author_link': "http://localhost:8000" + self.user.get_absolute_url(),
                'author_icon': "http://localhost:8000" + self.user.avatar.url,
                'color': 'good',
            }]
        )

    @patch('integration.models.SlackClient')
    def test_issue_modify(self, slackmock):
        # TODO TESTCASE broken test
        return
        issue = Issue()
        issue.title = "This is title"
        issue.project = self.project
        issue.save()

        self.selenium.get(
                '{}{}'.format(
                    self.live_server_url,
                    reverse('issue:edit', kwargs={'project': self.short, 'sqn_i': issue.number})
                    )
                )
        f = self.selenium.find_element_by_css_selector("input.select2-search__field").click()
        time.sleep(1)
        self.selenium.find_elements_by_css_selector('#select2-id_assignee-results li')[0].click()
        self.selenium.find_element_by_id('id_submit_edit').click()
        slackmock().api_call.assert_called_with(
            "chat.postMessage",
            channel="channel",
            attachments=[{
                'fallback': str(self.user) + " changed issue asdf-1 This is title.",
                'pretext': 'Issue changed:',
                'title': "asdf-1 This is title",
                'title_link': "http://localhost:8000/project/asdf/issue/1/",
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

    @patch('integration.models.SlackClient')
    def test_comment(self, slackmock):
        issue = Issue()
        issue.title = "This is title"
        issue.project = self.project
        issue.save()

        self.selenium.get(
                '{}{}'.format(
                    self.live_server_url,
                    reverse('issue:detail', kwargs={'project': self.project.name_short, 'sqn_i': issue.number})
                    )
                )
        f = self.selenium.find_element_by_id("id_text")
        f.send_keys("This is comment")
        self.selenium.find_element_by_name("action").click()
        slackmock().api_call.assert_called_with(
            "chat.postMessage",
            channel="channel",
            attachments=[{
                'fallback': str(self.user) + ' commented on "asdf-1 This is title".',
                'pretext': 'New comment:',
                'text': 'This is comment',
                'title': "asdf-1 This is title",
                'title_link': "http://localhost:8000/project/asdf/issue/1/",
                'author_name': str(self.user),
                'author_link': "http://localhost:8000" + self.user.get_absolute_url(),
                'author_icon': "http://localhost:8000" + self.user.avatar.url,
                'color': 'good',
            }]
        )

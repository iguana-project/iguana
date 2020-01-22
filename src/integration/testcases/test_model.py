"""
Iguana (c) by Marc Ammon, Moritz Fickenscher, Lukas Fridolin,
Michael Gunselmann, Katrin Raab, Christian Strate

Iguana is licensed under a
Creative Commons Attribution-ShareAlike 4.0 International License.

You should have received a copy of the license along with this
work. If not, see <http://creativecommons.org/licenses/by-sa/4.0/>.
"""
from collections import OrderedDict
import datetime

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse

from integration.models import SlackIntegration
from project.models import Project
from issue.models import Issue
from sprint.models import Sprint
from event import signals

from olea import parser


def cmp_deep(a, b):
    if type(a) != list and type(a) != dict:
        assert a == b, "{} != {}".format(a, b)
        return
    assert len(a) == len(b)
    if type(a) == list:
        for a_, b_ in zip(a, b):
            cmp_deep(a_, b_)
    if type(a) == dict:
        for key in a:
            cmp_deep(a[key], b[key])


class CallbackTestBase(TestCase):
    short = "proj"
    called = (0, None, None)

    @classmethod
    def setUpTestData(cls):
        # NOTE: if you modify those elements they need to be created in setUp, instead of here
        cls.user = get_user_model().objects.create_user('username', 'b', 'c')
        cls.user2 = get_user_model().objects.create_user('user2', 'x', 'y')
        cls.project = Project(creator=cls.user, name_short=cls.short)
        cls.project.save()
        cls.project.developer.set((cls.user.pk, cls.user2.pk))
        cls.project.manager.set((cls.user.pk,))
        cls.project.save()
        cls.issue = Issue()
        cls.issue.title = "sometitle"
        cls.issue.project = cls.project
        cls.issue.save()
        cls.issue.assignee.add(cls.user)
        cls.issue.save()
        cls.issue2 = Issue()
        cls.issue2.title = "othertitle"
        cls.issue2.project = cls.project
        cls.issue2.description = "foo"
        cls.issue2.save()
        cls.issue2.assignee.set([cls.user, cls.user2])
        cls.issue2.save()
        cls.sprint = Sprint(project=cls.project)
        cls.sprint.save()

    @classmethod
    def clean_callback(cls):
        cls.called = (0,)

    @classmethod
    def assertCalled(cls, *args, **kwargs):
        assert cls.called[0] == 1, "too many calls: %d instead of 1" % cls.called[0]
        for i, arg in enumerate(args):
            cmp_deep(arg, cls.called[1][i])
        for key in kwargs:
            cmp_deep(kwargs[key], cls.called[2][key])
        cls.clean_callback()

    @classmethod
    def assertNotCalled(cls):
        assert cls.called[0] == 0


class ConnectTest(CallbackTestBase):
    @classmethod
    def setUpTestData(self):
        super().setUpTestData()
        # Send an early signal to avoid event.signals.connector being called
        # later.
        signals.modify.send(sender=Issue)

        def callback(*args, **kwargs):
            self.called = (self.called[0] + 1, args, kwargs)
        self.si = SlackIntegration(api_token="token", channel="channel")
        self.si.on_issue_signal = callback
        self.si.on_sprint_signal = callback
        self.si.project = self.project
        self.si.save()  # this also connects the signals

    def setUp(self):
        self.clean_callback()

    def test_connect_signals(self):
        for signal in [signals.create, signals.modify]:
            signal.send(sender=Issue, somekey="someval")
            self.assertCalled(signal=signal, somekey="someval")
        for signal in [signals.start, signals.stop]:
            signal.send(sender=Sprint, somekey="someval")
            self.assertCalled(signal=signal, somekey="someval")

    def test_disconnect_late(self):
        '''
        Make sure that unsetting a notification actually disconnects the signal.
        '''
        self.si.notify_issue_create = False
        self.si.save()

        signals.modify.send(sender=Issue)
        self.assertCalled(signal=signals.modify)

        signals.create.send(sender=Issue)
        self.assertNotCalled()


class OnSignalTest(CallbackTestBase):
    @classmethod
    def setUpTestData(cls):
        signals.modify.send(sender=Issue)
        super().setUpTestData()

        class SlackMock:
            def api_call(innerself, *args, **kwargs):
                cls.called = (cls.called[0] + 1, args, kwargs)

        def slack_on(innerself, *args, **kwargs):
            if not innerself.slack:
                innerself.slack = SlackMock()

        cls.si = SlackIntegration(api_token="token", channel="channel")
        SlackIntegration.slack_on = slack_on
        cls.si.project = cls.project
        cls.si.save()

    def setUp(self):
        self.clean_callback()

    def test_wrong_project(self):
        p = Project(creator=self.user, name_short="foo")
        p.save()
        self.issue.project = p
        self.si.on_issue_signal(None, None, instance=self.issue)
        self.assertNotCalled()

    def test_start(self):
        self.sprint.startdate = datetime.time()
        self.si.on_sprint_signal(None, signals.start, instance=self.sprint, user=self.user)
        self.assertCalled(
            "chat.postMessage",
            channel="channel",
            attachments=[{
                'fallback': "username started sprint 1.",
                'pretext': 'Sprint started:',
                'text': "",
                'title': "Sprint 1",
                'title_link': "http://localhost:8000" + reverse("backlog:backlog",
                                                                kwargs={'project': self.project.name_short}),
                'author_name': "username",
                'author_link': "http://localhost:8000" + self.user.get_absolute_url(),
                'author_icon': "http://localhost:8000" + self.user.avatar.url,
                'fields': [
                    {"title": "Started", "value": "01/01/00", "short": True},
                ],
                'color': 'good',
            }]
        )

    def test_create(self):
        self.si.on_issue_signal(None, signals.create, instance=self.issue, user=self.user)
        self.assertCalled(
            "chat.postMessage",
            channel="channel",
            attachments=[{
                'fallback': "username created issue proj-1 sometitle.",
                'pretext': 'New Issue:',
                'text': "",
                'title': "proj-1 sometitle",
                'title_link': "http://localhost:8000" + self.issue.get_absolute_url(),
                'author_name': "username",
                'author_link': "http://localhost:8000" + self.user.get_absolute_url(),
                'author_icon': "http://localhost:8000" + self.user.avatar.url,
                'color': 'good',
            }]
        )

    def test_full_name(self):
        self.user.first_name = "First"
        self.user.last_name = "Last"
        self.user.save()

        self.si.on_issue_signal(None, signals.create, instance=self.issue, user=self.user)
        self.assertCalled(
            "chat.postMessage",
            channel="channel",
            attachments=[{
                'fallback': "First Last created issue proj-1 sometitle.",
                'pretext': 'New Issue:',
                'text': "",
                'title': "proj-1 sometitle",
                'title_link': "http://localhost:8000" + self.issue.get_absolute_url(),
                'author_name': "First Last",
                'author_link': "http://localhost:8000" + self.user.get_absolute_url(),
                'author_icon': "http://localhost:8000" + self.user.avatar.url,
                'color': 'good',
            }]
        )

        self.user.first_name = ""
        self.user.last_name = ""
        self.user.save()

    def test_modify(self):
        changed_data = OrderedDict()
        changed_data["title"] = "sometitle"
        changed_data["description"] = ""
        self.si.on_issue_signal(None, signals.modify, instance=self.issue2, user=self.user, changed_data=changed_data)
        self.assertCalled(
            "chat.postMessage",
            channel="channel",
            attachments=[{
                'fallback': "username changed issue proj-2 othertitle.",
                'pretext': 'Issue changed:',
                'title': "proj-2 othertitle",
                'title_link': "http://localhost:8000" + self.issue2.get_absolute_url(),
                'author_name': "username",
                'author_link': "http://localhost:8000" + self.user.get_absolute_url(),
                'author_icon': "http://localhost:8000" + self.user.avatar.url,
                'fields': [
                    {"title": "Title", "value": "sometitle → othertitle", "short": True},
                    {"title": "Description", "value": " → foo", "short": False},
                    ],
                'color': 'good',
            }]
        )

    def test_change_assignee(self):
        changed_data = OrderedDict()
        changed_data["assignee"] = "username"
        self.si.on_issue_signal(None, signals.modify, instance=self.issue2, user=self.user, changed_data=changed_data)
        self.assertCalled(
            "chat.postMessage",
            channel="channel",
            attachments=[{
                'fallback': "username changed issue proj-2 othertitle.",
                'pretext': 'Issue changed:',
                'title': "proj-2 othertitle",
                'title_link': "http://localhost:8000" + self.issue2.get_absolute_url(),
                'author_name': "username",
                'author_link': "http://localhost:8000" + self.user.get_absolute_url(),
                'author_icon': "http://localhost:8000" + self.user.avatar.url,
                'fields': [
                    {"title": "Assignee", "value": "{} → {}, {}".format(self.user, self.user2, self.user),
                     "short": True},
                    ],
                'color': 'good',
            }]
        )

    def test_change_title(self):
        # TODO TESTCASE
        # TODO including the previous and the new title
        pass

    def test_change_status(self):
        # TODO TESTCASE
        # NOTE: this might be a case where we don't want a message (it's not part of the issue itself)
        pass

    def test_change_type(self):
        # TODO TESTCASE
        # TODO including the previous and the new type
        pass

    def test_change_priority(self):
        # TODO TESTCASE
        # TODO including the previous and the new priority
        pass

    def test_change_description(self):
        # TODO TESTCASE
        # TODO including the previous and the new description
        pass

    def test_change_tags(self):
        # TODO TESTCASE
        # TODO including the previous and the new tags
        pass

    def test_create_issue_backlog_bar(self):
        parser.compile('sometitle :Task', self.issue.project, self.user)
        self.assertCalled(
            "chat.postMessage",
            channel="channel",
            attachments=[{
                'fallback': "username created issue proj-3 sometitle.",
                'pretext': 'New Issue:',
                'text': "",
                'title': "proj-3 sometitle",
                'title_link': "http://localhost:8000" + self.issue.get_absolute_url().replace("1", "3"),
                'author_name': "username",
                'author_link': "http://localhost:8000" + self.user.get_absolute_url(),
                'author_icon': "http://localhost:8000" + self.user.avatar.url,
                'color': 'good',
            }]
        )

    def test_create_issue_without_params_backlog_bar(self):
        parser.compile('sometitle', self.issue.project, self.user)
        self.assertCalled(
            "chat.postMessage",
            channel="channel",
            attachments=[{
                'fallback': "username created issue proj-4 sometitle.",
                'pretext': 'New Issue:',
                'text': "",
                'title': "proj-4 sometitle",
                'title_link': "http://localhost:8000" + self.issue.get_absolute_url().replace("1", "4"),
                'author_name': "username",
                'author_link': "http://localhost:8000" + self.user.get_absolute_url(),
                'author_icon': "http://localhost:8000" + self.user.avatar.url,
                'color': 'good',
            }]
        )

    def test_modify_issue_backlog_bar(self):
        parser.compile('>1 @user2', self.issue.project, self.user)
        self.assertCalled(
            "chat.postMessage",
            channel="channel",
            attachments=[{
                'fallback': "username changed issue proj-1 sometitle.",
                'pretext': 'Issue changed:',
                'title': "proj-1 sometitle",
                'title_link': "http://localhost:8000" + self.issue.get_absolute_url(),
                'author_name': "username",
                'author_link': "http://localhost:8000" + self.user.get_absolute_url(),
                'author_icon': "http://localhost:8000" + self.user.avatar.url,
                'fields': [
                    {"title": "Assignee", "value": "{} → {}, {}".format(self.user, self.user2, self.user),
                     "short": True},
                    ],
                'color': 'good',
            }]
        )

    def test_log_time(self):
        parser.compile('>1 +1m', self.issue.project, self.user)
        self.assertNotCalled()

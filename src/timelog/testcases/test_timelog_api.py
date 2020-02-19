"""
Iguana (c) by Marc Ammon, Moritz Fickenscher, Lukas Fridolin,
Michael Gunselmann, Katrin Raab, Christian Strate

Iguana is licensed under a
Creative Commons Attribution-ShareAlike 4.0 International License.

You should have received a copy of the license along with this
work. If not, see <http://creativecommons.org/licenses/by-sa/4.0/>.
"""
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
import json

from project.models import Project
from issue.models import Issue
from kanbancol.models import KanbanColumn
from django.contrib.auth import get_user_model


class TimelogApiTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        # NOTE: if you modify these elements they need to be created in setUp(), instead of here
        cls.user = get_user_model().objects.create_user('test', 'test@testing.com', 'test1234')
        cls.project = Project(creator=cls.user, name_short='PRJ')
        cls.project.save()
        cls.project.developer.add(cls.user)
        cls.project2 = Project(creator=cls.user, name_short='PRJ2')
        cls.project2.save()
        cls.project2.developer.add(cls.user)
        cls.kanbancol = KanbanColumn(project=cls.project, position=4, name='test')
        cls.kanbancol.save()
        cls.time = timezone.now().replace(microsecond=100000)
        cls.timestring = cls.time.strftime("%Y-%m-%d %H:%M:%S")
        cls.timestamp = cls.time.timestamp()

    def setUp(self):
        self.client.force_login(self.user)
        # NOTE: these elements get modified by some testcases, so they should NOT be created in setUpTestData()
        self.issue = Issue(project=self.project, due_date='2016-12-16', kanbancol=self.kanbancol, storypoints='3')
        self.issue.save()
        self.issue2 = Issue(project=self.project2, due_date='2016-12-16', kanbancol=self.kanbancol, storypoints='3')
        self.issue2.save()

    def test_view_and_template(self):
        # TODO TESTCASE see invite_users
        #      use view_and_template()
        # TODO which views?
        #      - timelog:api_last_7_days
        #      - timelog:api_activity
        #      - timelog:api_project_activity
        #      - timelog:api_logs_on_date
        #      - ...
        pass

    def test_redirect_to_login_and_login_required(self):
        self.client.logout()
        # TODO TESTCASE see invite_users
        #      redirect_to_login_and_login_required()
        # TODO which views?
        #      - timelog:api_last_7_days
        #      - timelog:api_activity
        #      - timelog:api_project_activity
        #      - timelog:api_logs_on_date
        #      - ...
        pass

    def test_user_passes_test_mixin(self):
        # TODO TESTCASE
        # TODO timelog:activity
        # TODO timelog:lastweek
        pass

    def test_api_activity_data(self):
        response = self.client.get(reverse('timelog:api_activity'))
        response = self.client.post(reverse('issue:log', kwargs={"project": self.issue.project.name_short,
                                                                 "sqn_i": self.issue.number}),
                                    {'time': '1h30m', 'created_at': self.timestring})
        response = self.client.get(reverse('timelog:api_activity'))
        response_json = response.json()
        self.assertEqual(response_json[str((self.time-timedelta(minutes=90)).timestamp())], 90.0)
        response = self.client.post(reverse('issue:log', kwargs={"project": self.issue.project.name_short,
                                                                 "sqn_i": self.issue.number}),
                                    {'time': '1h30m', 'created_at': self.timestring})
        response = self.client.get(reverse('timelog:api_activity'))
        response_json = response.json()
        self.assertEqual(response_json[str((self.time-timedelta(minutes=90)).timestamp())], 180.0)
        self.assertEqual(len(response_json), 4)
        newdate = self.time - timedelta(days=1)
        newdate_timestring = newdate.strftime("%Y-%m-%d %H:%M:%S")
        newdate_timestamp = newdate.timestamp()
        response = self.client.post(reverse('issue:log', kwargs={"project": self.issue.project.name_short,
                                                                 "sqn_i": self.issue.number}),
                                    {'time': '1h30m', 'created_at': newdate_timestring})
        response = self.client.get(reverse('timelog:api_activity'))
        response_json = response.json()
        self.assertEqual(response_json[str(newdate_timestamp)], 90.0)
        self.assertEqual(len(response_json), 5)

    def test_api_last_seven_days(self):
        response = self.client.get(reverse('timelog:api_last_7_days'))
        response_json = response.json()
        self.assertEqual(len(response_json), 0)

        response = self.client.post(reverse('issue:log', kwargs={"project": self.issue.project.name_short,
                                                                 "sqn_i": self.issue.number}),
                                    {'time': '1h30m', 'created_at': self.timestring})
        response = self.client.get(reverse('timelog:api_last_7_days'))
        response_json = response.json()
        self.assertEqual(len(response_json), 1)
        self.assertEqual(response_json[0]['fields']['time'], '01:30:00')

        newdate = self.time - timedelta(days=7)
        newdate_timestring = newdate.strftime("%Y-%m-%d %H:%M:%S")
        newdate_timestamp = newdate.timestamp()
        response = self.client.post(reverse('issue:log', kwargs={"project": self.issue.project.name_short,
                                                                 "sqn_i": self.issue.number}),
                                    {'time': '1h30m', 'created_at': newdate_timestring})
        response = self.client.get(reverse('timelog:api_last_7_days'))
        response_json = response.json()
        self.assertEqual(len(response_json), 1)

    def test_api_specific_date(self):
        response = self.client.post(reverse('issue:log',
                                            kwargs={"project": self.issue.project.name_short,
                                                    "sqn_i": self.issue.number}),
                                    {'time': '1m', 'created_at': self.timestring})
        string_date = str(self.time.date()).replace("-", "")
        response = self.client.get(reverse('timelog:api_logs_on_date', kwargs={"date": string_date}))
        response_json = response.json()
        self.assertEqual(len(response_json), 1)
        newdate = self.time - timedelta(days=1)
        string_date = str(newdate.date()).replace("-", "")
        response = self.client.get(reverse('timelog:api_logs_on_date', kwargs={"date": string_date}))
        response_json = response.json()
        self.assertEqual(len(response_json), 0)

        response = self.client.get(reverse('timelog:api_logs_on_date', kwargs={"date": "200170418"}))
        response_json = response.json()
        self.assertEqual(response_json, "incorrect Date format: YYYYMMDD")

        response = self.client.get(reverse('timelog:api_logs_on_date', kwargs={"date": "20171318"}))
        response_json = response.json()
        self.assertEqual(response_json, "incorrect Date format: YYYYMMDD")

    def test_api_project_activity(self):
        response = self.client.get(reverse('timelog:api_project_activity'))
        response_json = response.json()
        self.assertEqual(response_json, "You need to pass a GET Paramter 'project'")

        response = self.client.post(reverse('issue:log',
                                            kwargs={"project": self.issue.project.name_short,
                                                    "sqn_i": self.issue.number}),
                                    {'time': '1m', 'created_at': self.timestring})
        response = self.client.get(reverse('timelog:api_project_activity')+"?project="+self.project.name_short)
        response_json = response.json()
        self.assertEqual(len(response_json), 32)
        self.assertEqual(response_json[31]['val'], 60.0)

        response = self.client.get(
                reverse('timelog:api_project_activity')+"?project="+self.project.name_short+"&delta=1")
        response_json = response.json()
        self.assertEqual(len(response_json), 32)
        self.assertEqual(response_json[31]['val'], 0)

    def test_api_logged_out(self):
        self.client.logout()
        response = self.client.get(reverse('timelog:api_last_7_days'))
        response_json = response.json()
        self.assertEqual(response_json, 'login!')

        response = self.client.get(reverse('timelog:api_activity'))
        response_json = response.json()
        self.assertEqual(response_json, 'login!')

        response = self.client.get(reverse('timelog:api_logs_on_date', kwargs={"date": "200170418"}))
        response_json = response.json()
        self.assertEqual(response_json, 'login!')

        response = self.client.get(reverse('timelog:api_project_activity')+"?project="+self.project.name_short)
        response_json = response.json()
        self.assertEqual(response_json, "You're not Member of this Project, or login!")

    def test_project_filter(self):
        response = self.client.post(reverse('issue:log', kwargs={"project": self.issue.project.name_short,
                                                                 "sqn_i": self.issue.number}),
                                    {'time': '1m', 'created_at': self.timestring})
        response = self.client.get(reverse('timelog:api_activity')+'?project='+self.project.name_short)
        response_json = response.json()
        self.assertEqual(response_json[str((self.time-timedelta(minutes=1)).timestamp())], 1.0)

        response = self.client.get(reverse('timelog:api_activity')+'?project='+self.project2.name_short)
        response_json = response.json()
        self.assertEqual(len(response_json), 3)

        response = self.client.get(reverse('timelog:api_last_7_days')+'?project='+self.project.name_short)
        response_json = response.json()
        self.assertEqual(len(response_json), 1)

        response = self.client.get(reverse('timelog:api_last_7_days')+'?project='+self.project2.name_short)
        response_json = response.json()
        self.assertEqual(len(response_json), 0)

        string_date = str(self.time.date()).replace("-", "")
        response = self.client.get(reverse('timelog:api_logs_on_date',
                                           kwargs={"date": string_date}
                                           )+'?project='+self.project.name_short)
        response_json = response.json()
        self.assertEqual(len(response_json), 1)

        response = self.client.get(reverse('timelog:api_logs_on_date',
                                           kwargs={"date": string_date}
                                           )+'?project='+self.project2.name_short)
        response_json = response.json()
        self.assertEqual(len(response_json), 0)

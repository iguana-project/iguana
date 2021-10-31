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
from django.utils.timezone import now
from datetime import timedelta

from common.testcases.generic_testcase_helper import user_doesnt_pass_test_and_gets_404
from issue.models import Issue
from kanbancol.models import KanbanColumn
from project.models import Project
from timelog.templatetags.filter import duration
from timelog.models import Timelog
from django.contrib.auth import get_user_model


class TimelogTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        # NOTE: if you modify these elements they need to be created in setUp(), instead of here
        cls.user = get_user_model().objects.create_user('test', 'test@testing.com', 'test1234')
        cls.user2 = get_user_model().objects.create_user('test2', 'test@testing2.com', 'test1234')
        cls.user.save()
        cls.user2.save()

    def setUp(self):
        self.client.force_login(self.user)
        # NOTE: these elements get modified by some testcases, so they should NOT be created in setUpTestData()
        self.project = Project(creator=self.user, name_short='PRJ', activity_only_for_managers=False)
        self.project.save()
        self.project.developer.add(self.user)

        self.project2 = Project(creator=self.user, activity_only_for_managers=True, name_short='PRJJ')
        self.project2.save()
        self.project2.manager.add(self.user)
        self.project2.developer.add(self.user, self.user2)

        self.kanbancol = KanbanColumn(project=self.project, position=4, name='test')
        self.kanbancol.save()
        self.issue = Issue(title='a very very very very very very very long issue title',
                           project=self.project,
                           due_date='2016-12-16',
                           kanbancol=self.kanbancol,
                           storypoints='3'
                           )
        self.issue.save()
        self.issue.assignee.add(self.user)
        self.issue2 = Issue(title='second_issue', project=self.project)
        self.issue2.save()
        self.issue2.assignee.add(self.user)
        self.time = now().strftime("%Y-%m-%d %H:%M:%S")

    def test_view_and_template(self):
        # TODO TESTCASE see invite_users
        #      use view_and_template()
        # TODO which views?
        #      - timelog:loginfo
        #      - timelog:archiv
        #      - issue:log
        #      - issue:logs with (?P<sqn_l>[0-9]+)/edit/ (logedit)
        #      - issue:logs with  (?P<sqn_l>[0-9]+)/delete/? (logdelete)
        #      - issue:logedit
        #      - issue:logdelete
        #      - ProjectUserTimelogView - project:usertimelog
        #      - ProjectDetailTimelogView - project:timelog
        #      - ...
        pass

    def test_redirect_to_login_and_login_required(self):
        self.client.logout()
        # TODO TESTCASE see invite_users
        #      redirect_to_login_and_login_required()
        # TODO which views?
        #      - timelog:loginfo
        #      - timelog:archiv
        #      - issue:log
        #      - issue:logs with (?P<sqn_l>[0-9]+)/edit/ (logedit)
        #      - issue:logs with  (?P<sqn_l>[0-9]+)/delete/? (logdelete)
        #      - issue:logedit
        #      - issue:logdelete
        #      - ProjectUserTimelogView - project:usertimelog
        #      - ProjectDetailTimelogView - project:timelog
        #      - ...
        pass

    def test_user_passes_test_mixin(self):
        # TODO TESTCASE
        #      - timelog:loginfo
        #      - timelog:archiv
        #      - issue:log
        #      - issue:logs with (?P<sqn_l>[0-9]+)/edit/ (logedit)
        #      - issue:logs with  (?P<sqn_l>[0-9]+)/delete/? (logdelete)
        #      - issue:logedit
        #      - issue:logdelete
        #      - ProjectUserTimelogView - project:usertimelog
        #      - ProjectDetailTimelogView - project:timelog
        #      - ...
        pass

    def test_log_time_and_redirect(self):
        response = self.client.post(reverse('issue:log', kwargs={"project": self.issue.project.name_short,
                                                                 "sqn_i": self.issue.number}),
                                    {'time': '1h30m', 'created_at': self.time},
                                    follow=True)
        self.assertRedirects(response, reverse('issue:detail', kwargs={'project': self.project.name_short,
                                                                       'sqn_i': 1}))

    # PER USER START
    def test_timelog_loginfo_per_user_only_visible_for_own_user(self):
        response = self.client.post(reverse('issue:log', kwargs={"project": self.issue.project.name_short,
                                                                 "sqn_i": self.issue.number}),
                                    {'time': '1h30m', 'created_at': self.time},
                                    follow=True)
        response = self.client.get(reverse('timelog:loginfo'))
        self.assertContains(response, "1 Hour and 30 Minutes")

        # tag filter issue title short
        self.assertContains(response, "...")

        self.client.logout()
        self.client.force_login(self.user2)

        response = self.client.post(reverse('issue:log', kwargs={"project": self.issue.project.name_short,
                                                                 "sqn_i": self.issue.number,
                                                                 }),
                                    {'time': '15m', 'created_at': self.time})
        self.client.logout()
        self.client.force_login(self.user)
        response = self.client.get(reverse('timelog:loginfo'))
        # first log
        self.assertContains(response, "1 Hour and 30 Minutes")
        # second log - different user
        self.assertNotContains(response, "15 Minutes")

    def test_timelog_loginfo_and_issue_loginfo_log_time_in_multiple_issues_and_projects_for_own_user(self):
        response = self.client.post(reverse('issue:log', kwargs={"project": self.issue.project.name_short,
                                                                 "sqn_i": self.issue.number}),
                                    {'time': '1h30m', 'created_at': self.time},
                                    follow=True)
        response = self.client.post(reverse('issue:log', kwargs={"project": self.issue.project.name_short,
                                                                 "sqn_i": self.issue2.number}),
                                    {'time': '15m', 'created_at': self.time},
                                    follow=True)
        response = self.client.get(reverse('timelog:loginfo'))
        # first log
        self.assertContains(response, "1 Hour and 30 Minutes")
        # second log - second issue
        self.assertContains(response, "15 Minutes")

        project2 = Project(creator=self.user, name_short='PRJ2')
        project2.save()
        project2.developer.add(self.user)
        # both are shown in timelog:loginfo
        response = self.client.get(reverse('timelog:loginfo'))
        self.assertContains(response, "1 Hour and 30 Minutes")
        self.assertContains(response, "15 Minutes")

        # additional log for a different project
        issue3 = Issue(title='third_issue', project=project2)
        issue3.save()
        issue3.assignee.add(self.user)
        response = self.client.post(reverse('issue:log', kwargs={"project": project2.name_short,
                                                                 "sqn_i": issue3.number}),
                                    {'time': '20m', 'created_at': self.time},
                                    follow=True)

        # all three are shown in timelog:loginfo
        response = self.client.get(reverse('timelog:loginfo'))
        self.assertContains(response, "1 Hour and 30 Minutes")
        self.assertContains(response, "15 Minutes")
        self.assertContains(response, "20 Minutes")

    # PER ISSUE START
    def test_log_time_per_issue_even_from_other_user(self):
        response = self.client.post(reverse('issue:log', kwargs={"project": self.issue.project.name_short,
                                                                 "sqn_i": self.issue.number}),
                                    {'time': '1h30m', 'created_at': self.time})
        response = self.client.post(reverse('issue:log', kwargs={"project": self.issue.project.name_short,
                                                                 "sqn_i": self.issue.number}),
                                    {'time': '15m', 'created_at': self.time})
        self.client.logout()
        self.project.developer.add(self.user2)
        self.issue.assignee.add(self.user2)
        self.client.force_login(self.user2)
        # second user log
        response = self.client.post(reverse('issue:log', kwargs={"project": self.issue.project.name_short,
                                                                 "sqn_i": self.issue.number}),
                                    {'time': '20m', 'created_at': self.time})
        response = self.client.get(reverse('issue:detail', kwargs={"project": self.issue.project.name_short,
                                                                   "sqn_i": self.issue.number}))
        # first log -  first user
        self.assertContains(response, "1 Hour and 30 Minutes")
        # second log - first user
        self.assertContains(response, "15 Minutes")
        # third log - second user
        self.assertContains(response, "20 Minutes")

    def test_log_time_in_future_fails(self):
        response = self.client.post(reverse('issue:log', kwargs={"project": self.issue.project.name_short,
                                                                 "sqn_i": self.issue.number}),
                                    {'time': '1h30m',
                                     'created_at': (now() + timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S")})
        self.assertEqual(response.status_code, 200)
        # still on the same page (issue:log)
        self.assertTemplateUsed(response, 'timelog/timelog_create.html')
        self.assertContains(response, 'The date entered must be today or lesser.')

    def test_log_time_delete_log_per_issue(self):
        response = self.client.post(reverse('issue:log', kwargs={"project": self.issue.project.name_short,
                                                                 "sqn_i": self.issue.number}),
                                    {'time': '1h30m', 'created_at': self.time})
        response = self.client.post(reverse('issue:log', kwargs={"project": self.issue.project.name_short,
                                                                 "sqn_i": self.issue.number}),
                                    {'time': '2h', 'created_at': self.time})

        response = self.client.post(reverse('issue:logdelete', kwargs={"project": self.issue.project.name_short,
                                                                       "sqn_i": self.issue.number,
                                                                       "sqn_l": 2}),
                                    {'delete': 'true'}, follow=True)
        self.assertTemplateUsed(response, 'timelog/timelog_list_peruser.html')
        self.assertContains(response, "1 Hour and 30 Minutes")
        self.assertNotContains(response, "2 Hours")

    def test_log_time_keep_log_per_issue(self):
        response = self.client.post(reverse('issue:log', kwargs={"project": self.issue.project.name_short,
                                                                 "sqn_i": self.issue.number}),
                                    {'time': '1h30m', 'created_at': self.time})
        response = self.client.post(reverse('issue:logdelete', kwargs={"project": self.issue.project.name_short,
                                                                       "sqn_i": self.issue.number,
                                                                       "sqn_l": 1}),
                                    {'keep': 'true'}, follow=True)
        self.assertTemplateUsed(response, 'timelog/timelog_list_peruser.html')
        self.assertContains(response, "1 Hour and 30 Minutes")

    def test_log_time_edit_log_per_issue(self):
        response = self.client.post(reverse('issue:log', kwargs={"project": self.issue.project.name_short,
                                                                 "sqn_i": self.issue.number}),
                                    {'time': '1d1h30m', 'created_at': self.time})

        response = self.client.get(reverse('issue:detail', kwargs={"project": self.issue.project.name_short,
                                                                   "sqn_i": self.issue.number}))
        self.assertContains(response, "1 Day, 1 Hour and 30 Minutes")

        response = self.client.get(reverse('issue:logedit',
                                           kwargs={"project": self.issue.project.name_short,
                                                   "sqn_i": self.issue.number, "sqn_l": 1}))
        self.assertContains(response, "1d 1h 30m")

        response = self.client.post(reverse('issue:logedit', kwargs={"project": self.issue.project.name_short,
                                                                     "sqn_i": self.issue.number, "sqn_l": 1}),
                                    {'time': '3h', 'created_at': self.time, 'save_timelog_change': 'true'})
        response = self.client.get(reverse('issue:detail', kwargs={"project": self.issue.project.name_short,
                                                                   "sqn_i": self.issue.number}))
        self.assertContains(response, "3 Hours")

        # test to edit with other user - should not be possible
        self.client.logout()
        self.client.force_login(self.user2)

        user_doesnt_pass_test_and_gets_404(self, 'issue:logedit',
                                           address_kwargs={"project": self.issue.project.name_short,
                                                           "sqn_i": self.issue.number, "sqn_l": 1})

    # PROJECT START
    def test_project_detail_timelog_from_different_issuesss_of_project_even_from_other_users(self):
        cases = ['2d 2h 5m', '1d 1h 5m', '2d 5m', '1d 3h']
        mappings = ['2 Days, 2 Hours and 5 Minutes', '1 Day, 1 Hour and 5 Minutes',
                    '2 Days and 5 Minutes', '1 Day and 3 Hours']
        sums = ['3 Days, 3 Hours and 10 Minutes', '3 Days, 3 Hours and 5 Minutes']
        # first user, first issue
        response = self.client.post(reverse('timelog:loginfo'),
                                    {'time': cases[0], 'created_at': self.time, 'issue': self.issue.id},
                                    follow=True)
        # first user, second issue
        response = self.client.post(reverse('timelog:loginfo'),
                                    {'time': cases[1], 'created_at': self.time, 'issue': self.issue2.id},
                                    follow=True)
        self.client.logout()
        self.project.developer.add(self.user2)
        self.issue.assignee.add(self.user2)
        self.issue2.assignee.add(self.user2)
        self.client.force_login(self.user2)
        # second user
        # first user, first issue
        response = self.client.post(reverse('timelog:loginfo'),
                                    {'time': cases[2], 'created_at': self.time, 'issue': self.issue.id},
                                    follow=True)
        # first user, second issue
        response = self.client.post(reverse('timelog:loginfo'),
                                    {'time': cases[3], 'created_at': self.time, 'issue': self.issue2.id},
                                    follow=True)

        response = self.client.get(reverse('project:timelog', kwargs={"project": self.issue.project.name_short}))
        for user in self.project.developer.all():
            self.assertContains(response, user.username)

        for i in range(4):
            self.assertContains(response, mappings[i])

        # sums of both users
        self.assertContains(response, 'total: '+sums[0])
        self.assertContains(response, 'total: '+sums[1])

    def test_project_detail_timelog_username_appears(self):
        for dev in self.project.developer.all():
            response = self.client.get(reverse('project:usertimelog', kwargs={"project": self.issue.project.name_short,
                                                                              "username": dev.username}))
        self.assertContains(response, dev.username)

    def test_timelog_edit_render_value_issue_logedit(self):
        cases = ['1d 1h 5m', '1d 5m', '1d 3h',
                 '1h 5m', '1d', '3h', '5m'
                 ]
        for i in range(len(cases)):
            response = self.client.post(reverse('timelog:loginfo'),
                                        {'time': cases[i], 'created_at': self.time, 'issue': self.issue.id},
                                        follow=True)
            response = self.client.get(reverse('issue:logedit',
                                               kwargs={"project": self.issue.project.name_short,
                                                       "sqn_i": self.issue.number, "sqn_l": i+1}))
            self.assertContains(response, cases[i])

    def test_timelog_loginfo(self):
        cases = ['2d 2h 5m', '1d 1h 5m', '1d 5m', '1d 3h',
                 '1h 5m', '1d', '3h', '5m', '1m'
                 ]
        for i in range(len(cases)):
            response = self.client.post(reverse('timelog:loginfo'),
                                        {'time': cases[i], 'created_at': self.time, 'issue': self.issue.id},
                                        follow=True)
            log = Timelog.objects.get(id=i+1)
            response = self.client.get(reverse('timelog:loginfo'))
            self.assertContains(response, duration(log.time))

    def test_timelog_model_str_method(self):
        response = self.client.post(reverse('timelog:loginfo'),
                                    {'time': '2h30m', 'created_at': self.time, 'issue': self.issue.id},
                                    follow=True)
        log = Timelog.objects.get(id=1)
        self.assertEqual(str(log), "logged time: {} for issue: {}".format(log.time, log.issue))

    def test_project_timelogs_only_for_manager_setting(self):
        response = self.client.get(reverse('project:timelog', kwargs={"project": self.project2.name_short}))
        for user in self.project2.developer.all():
            self.assertContains(response, user.username)
        response = self.client.get(reverse('project:usertimelog',
                                   kwargs={"project": self.project2.name_short, "username": self.user2.username}),
                                   follow=True)
        self.assertContains(response, self.user2.username)
        self.client.force_login(self.user2)
        response = self.client.get(reverse('project:timelog', kwargs={"project": self.project2.name_short}))
        self.assertRedirects(response,
                             reverse('project:usertimelog',
                                     kwargs={"project": self.project2.name_short, "username": self.user2.username}
                                     )
                             )
        response = self.client.get(reverse('project:usertimelog',
                                   kwargs={"project": self.project2.name_short, "username": self.user.username}),
                                   follow=True)
        self.assertRedirects(response,
                             reverse('project:usertimelog',
                                     kwargs={"project": self.project2.name_short, "username": self.user2.username}
                                     )
                             )
        self.project2.activity_only_for_managers = False
        self.project2.save()
        response = self.client.get(reverse('project:timelog', kwargs={"project": self.project2.name_short}))
        for user in self.project2.developer.all():
            self.assertContains(response, user.username)
        response = self.client.get(reverse('project:usertimelog',
                                   kwargs={"project": self.project2.name_short, "username": self.user.username}),
                                   follow=True)
        self.assertContains(response, self.user.username)

    def test_timelog_archiv(self):
        response = self.client.get(reverse('timelog:archiv'))
        response = self.client.get(reverse('timelog:archiv')+'?page=2')

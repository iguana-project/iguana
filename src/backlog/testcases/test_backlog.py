"""
Iguana (c) by Marc Ammon, Moritz Fickenscher, Lukas Fridolin,
Michael Gunselmann, Katrin Raab, Christian Strate

Iguana is licensed under a
Creative Commons Attribution-ShareAlike 4.0 International License.

You should have received a copy of the license along with this
work. If not, see <http://creativecommons.org/licenses/by-sa/4.0/>.
"""
from django.test import TestCase
from django.views.generic import View

from django.contrib.auth import get_user_model

from backlog.views import BacklogListView
from project.models import Project
from sprint.models import Sprint
from common.testcases.generic_testcase_helper import view_and_template, redirect_to_login_and_login_required


# TODO see sprint/testcases/test_sprint.py for already existing tests and move them if there are only-backlog-tests
class BacklogTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        # NOTE: if you modify this element it needs to be created in setUp, instead of here
        cls.user = get_user_model().objects.create_user('django', 'django@example.com', 'unchained')

    def setUp(self):
        self.project = Project(creator=self.user, name_short='PRJ')
        self.project.save()
        self.project.developer.add(self.user)
        # TODO hopefully this will correctly create this sprint as already completed.
        self.sprint = Sprint(project=self.project, seqnum=3, startdate='2016-03-04', enddate='2016-03-05')
        self.sprint.save()
        self.client.force_login(self.user)

    def test_view_and_template(self):
        # general backlog
        view_and_template(self, BacklogListView, 'backlog/backlog_list.html', 'backlog:backlog',
                          address_kwargs={'project': self.project.name_short})
        # backlog for specific sprint
        view_and_template(self, BacklogListView, 'backlog/backlog_list.html', 'backlog:backlog',
                          address_kwargs={'project': self.project.name_short, 'sqn_s': 3})

    def test_redirect_to_login_and_login_required(self):
        self.client.logout()
        # general backlog
        redirect_to_login_and_login_required(self, 'backlog:backlog',
                                             address_kwargs={'project': self.project.name_short})
        # backlog for specific sprint
        redirect_to_login_and_login_required(self, 'backlog:backlog',
                                             address_kwargs={'project': self.project.name_short, 'sqn_s': 3})

    def test_backlog_list(self):
        # TODO TESTCASE
        # TODO see sprint/testcases/test_sprint.py for already existing tests
        #      and move them if there are only-backlog-tests
        pass

    def test_list_current_sprint(self):
        # TODO TESTCASE
        # TODO see sprint/testcases/test_sprint.py for already existing tests
        #      and move them if there are only-backlog-tests
        pass

    # TODO see sprint/testcases/test_sprint.py for already existing tests and move them if there are only-backlog-tests
    def test_list_different_sprint(self):
        # TODO TESTCASE
        # NOTE: another sprint has to exist to be showable
        pass

    # TODO see sprint/testcases/test_sprint.py for already existing tests and move them if there are only-backlog-tests
    def test_move_issue_to_current_sprint(self):
        # TODO TESTCASE
        pass

    # TODO see sprint/testcases/test_sprint.py for already existing tests and move them if there are only-backlog-tests
    def test_remove_issue_from_current_sprint(self):
        # TODO TESTCASE
        pass

    # TODO see sprint/testcases/test_sprint.py for already existing tests and move them if there are only-backlog-tests
    def test_order_by(self):
        # TODO TESTCASE for both backlog_list and current sprint for multiple order-by-situations
        pass

    # TODO see sprint/testcases/test_sprint.py for already existing tests and move them if there are only-backlog-tests
    def test_issue_short_names_are_shown(self):
        # TODO TESTCASE
        pass

    # TODO see sprint/testcases/test_sprint.py for already existing tests and move them if there are only-backlog-tests
    def test_issue_names_are_shown(self):
        # TODO TESTCASE
        pass

    # TODO see sprint/testcases/test_sprint.py for already existing tests and move them if there are only-backlog-tests
    def test_issues_types_are_shown(self):
        # TODO TESTCASE
        pass

    # TODO see sprint/testcases/test_sprint.py for already existing tests and move them if there are only-backlog-tests
    def test_user_are_shown(self):
        # TODO TESTCASE
        pass

    # TODO see sprint/testcases/test_sprint.py for already existing tests and move them if there are only-backlog-tests
    def test_priorities_are_shown(self):
        # TODO TESTCASE
        pass

    def test_show_done_issues_in_finished_sprints(self):
        # TODO TESTCASE
        # TODO write a test as soon as this feature is implemented - IGU-399
        pass

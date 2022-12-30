"""
Iguana (c) by Marc Ammon, Moritz Fickenscher, Lukas Fridolin,
Michael Gunselmann, Katrin Raab, Christian Strate

Iguana is licensed under a
Creative Commons Attribution-ShareAlike 4.0 International License.

You should have received a copy of the license along with this
work. If not, see <http://creativecommons.org/licenses/by-sa/4.0/>.
"""
from django.urls import reverse
from rest_framework.test import APIClient, APITestCase
from rest_framework import status

from common.testcases.generic_testcase_helper import number_of_objects_with_read_permission
from project.models import Project
from issue.models import Issue, Comment
from timelog.models import Timelog
from timelog.forms import DurationWidget
from user_management.models import CustomUser
from django.contrib.auth import get_user_model
from django.db.models import Q

import base64
import json
import datetime
import re


class ApiTest(APITestCase):
    @classmethod
    def setUpTestData(cls):
        # NOTE: if you modify these elements they need to be created in setUp(), instead of here
        cls.user1 = get_user_model().objects.create_user('user1', 'mail', 'c')
        cls.user2 = get_user_model().objects.create_user('user2', 'othermail', 'c')
        cls.user3 = get_user_model().objects.create_user('user3', 'foothermail', 'c')
        # needed to transform the internal datetime.timedelta representation to the one used in the api
        cls.transform_time_format = DurationWidget()

    def setUp(self):
        # NOTE: these elements get modified by some testcases, so they should NOT be created in setUpTestData()
        self.project = Project(creator=self.user1, name_short='asdf', name="first project")
        self.project.save()
        self.project.developer.add(self.user1)
        self.project.developer.add(self.user2)
        self.project.manager.add(self.user1)
        self.project.manager.add(self.user3)
        self.issue = Issue(title='test', project=self.project)
        self.issue.save()
        self.comment = Comment(text='test', creator=self.user1, issue=self.issue)
        self.comment.save()
        self.log = Timelog(time=datetime.timedelta(hours=2), user=self.user1, issue=self.issue)
        self.log.save()
        self.client.credentials(HTTP_AUTHORIZATION='Basic ' + base64.b64encode('user1:c'.encode()).decode())
        # an issue that has no members yet
        self.issue_new = Issue(title='new_issue_title', project=self.project)
        self.issue_new.save()
        # another issue that has no members yet
        self.issue_new2 = Issue(title='new_issue_title2', project=self.project)
        self.issue_new2.save()

        # kwargs
        self.short_name_kwargs = {'name_short': self.project.name_short}
        self.project_name_kwargs = {'project': self.project.name_short}
        self.issue_number_kwargs = {'project': self.project.name_short,
                                    'number': self.issue.number}
        self.issue_number2_kwargs = {'project': self.project.name_short,
                                     'issue': self.issue.number}
        self.timelog_number_kwargs = {'project': self.project.name_short,
                                      'issue': self.issue.number,
                                      'number': self.log.number}
        self.comment_seqnum_kwargs = {'project': self.project.name_short,
                                      'issue': self.issue.number,
                                      'seqnum': self.comment.seqnum}

    # change user and credentials used for api authorization
    def use_user(self, user_to_be_logged_in):
        # all user use 'c' as password
        self.client.credentials(HTTP_AUTHORIZATION='Basic ' +
                                base64.b64encode((str(user_to_be_logged_in)+':c').encode()).decode())

    # compares two lists of issues with each other - one of them is a list of json, the other a list of internal objects
    # \param issues_responded The issue list in json format returned from an api call
    # \param issues_internal The issue list from the database
    def compare_issue_lists(self, issues_responded, issues_internal):
        self.assertEqual(len(issues_responded), len(issues_internal))
        for i in range(len(issues_responded)):
            # title
            self.assertEqual(issues_responded[i]['title'], issues_internal[i].title)
            # project
            self.assertEqual(issues_responded[i]['project'], issues_internal[i].project.name)
            # assignee
            self.assertEqual(issues_responded[i]['assignee'],
                             [issue.username for issue in list(issues_internal[i].assignee.all())])

    # check whether the provided user is assigned to the expected amount of issues
    def validate_issues_assigned(self, user, list_of_issues):
        # use the provided user for the api request
        self.use_user(user)
        # check assignments on the model data
        self.assertEqual(list(Issue.objects.filter(assignee=user)), list_of_issues)

        # api response
        response = self.client.get(reverse('api:issues-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()['count'], len(list_of_issues))
        # compare the two lists with each other
        self.compare_issue_lists(response.json()['results'], list_of_issues)

    def test_get_issues(self):
        list_of_issues1 = []
        list_of_issues2 = []
        # preconditions neither user1 nor user2 is assignee of an issue
        self.validate_issues_assigned(self.user1, list_of_issues1)
        self.validate_issues_assigned(self.user2, list_of_issues2)

        # assign user1 to issue_new; this has no effect for user2
        self.issue_new.assignee.add(self.user1)
        list_of_issues1 += [self.issue_new]
        self.validate_issues_assigned(self.user1, list_of_issues1)
        self.validate_issues_assigned(self.user2, list_of_issues2)

        # assign user2 to issue_new2; this has no effect for user1
        self.issue_new2.assignee.add(self.user2)
        list_of_issues2 += [self.issue_new2]
        self.validate_issues_assigned(self.user1, list_of_issues1)
        self.validate_issues_assigned(self.user2, list_of_issues2)

        # assign user1 to issue_new2; this has no effect for user2
        self.issue_new2.assignee.add(self.user1)
        list_of_issues1 += [self.issue_new2]
        self.validate_issues_assigned(self.user1, list_of_issues1)
        self.validate_issues_assigned(self.user2, list_of_issues2)

    # checks whether the provided user has read access to all provided projects
    def validate_projects_readable(self, user, expected_num_of_projects, list_of_projs):
        self.use_user(user)
        response = self.client.get(reverse('api:project-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()['count'], expected_num_of_projects)
        self.assertEqual(number_of_objects_with_read_permission(Project, user), expected_num_of_projects)
        # alternative check - the previous one checks whether read permissions are correctly used though
        # read permissions for a project should exist for developer and manager
        self.assertEqual(list(Project.objects.filter(Q(developer=user) | Q(manager=user)).distinct()), list_of_projs)

    def test_get_projects(self):
        # user1 is developer and manager of project - this should only add up to 1 project
        expected_num_of_projects1 = 1
        expected_num_of_projects2 = 1
        expected_num_of_projects3 = 1
        self.validate_projects_readable(self.user1, expected_num_of_projects1, [self.project])

        # user2 is only developer of project
        self.validate_projects_readable(self.user2, expected_num_of_projects2, [self.project])

        # user3 is only manager of project "second project"
        self.validate_projects_readable(self.user3, expected_num_of_projects3, [self.project])

        # add user1 to project_new
        project_new = Project(creator=self.user1, name_short='2nd', name="second project")
        project_new.save()
        project_new.developer.add(self.user1)
        # this should not change the checks for user2 and user3 only for user1
        expected_num_of_projects1 += 1
        self.validate_projects_readable(self.user1, expected_num_of_projects1, [self.project, project_new])
        self.validate_projects_readable(self.user2, expected_num_of_projects2, [self.project])
        self.validate_projects_readable(self.user3, expected_num_of_projects3, [self.project])

        project_new2 = Project(creator=self.user3, name_short='3rd', name="third project")
        project_new2.save()
        # being a creator doesn't add read permissions
        self.validate_projects_readable(self.user3, expected_num_of_projects3, [self.project])
        # add user3 to project_new2 "third project"
        project_new2.manager.add(self.user3)
        expected_num_of_projects3 += 1
        self.validate_projects_readable(self.user1, expected_num_of_projects1, [self.project, project_new])
        self.validate_projects_readable(self.user2, expected_num_of_projects2, [self.project])
        self.validate_projects_readable(self.user3, expected_num_of_projects3, [self.project, project_new2])

    # compares two lists of timelogs with each other - one of them is a list of json,
    #                                                  the other a list of internal objects
    # compares status code, project name, issue name, user name, time logged
    # \param timelogs_responded The timelogs list in json format returned from an api call
    # \param timelogs_internal The timelogs list from the database
    # \param user=None when all timelogs should only be from that provided user,
    #        otherwise the comparison takes place with the provided list
    def compare_timelog_lists(self, timelogs_responded, timelogs_internal, user=None):
        self.assertEqual(len(timelogs_responded), len(timelogs_internal))
        for i in range(len(timelogs_responded)):
            response_time_log = timelogs_responded[i]
            time_log = timelogs_internal[i]
            issue = time_log.issue
            project_name = issue.project.name_short
            # check project and issue of time log
            self.assertRegex(response_time_log['issue'], project_name + r"-\d+ " + issue.title)
            # check user name
            # only check whether it is the "own" user when the parameter is provided
            if user:
                self.assertEqual(response_time_log['user'], user.username)
            else:
                self.assertEqual(response_time_log['user'], time_log.user.username)
            # check time
            time = self.transform_time_format.format_value(time_log.time)
            self.assertEqual(response_time_log['time'], time)

    # checks timelogs: status code, project name, issue name, user name, time logged
    # \param user: the user that should have the time logs
    # \param time_logs: list of time logs
    def validate_timelogs(self, user, time_logs):
        self.use_user(user)
        response = self.client.get(reverse('api:timelogs-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()['count'], len(time_logs))
        # we wanna make sure that only timelogs of "user" are in the list
        self.compare_timelog_lists(response.json()['results'], time_logs, user)

    def test_get_timelogs(self):
        expected_time_logs = [self.log]
        self.validate_timelogs(self.user1, expected_time_logs)

        # add second time log
        log = Timelog(issue=self.issue_new, user=self.user1, time=datetime.timedelta(hours=2))
        log.save()
        expected_time_logs += [log]
        self.validate_timelogs(self.user1, expected_time_logs)

        # other user have no entries (shouldn't be visible)
        expected_time_logs = []
        self.validate_timelogs(self.user2, expected_time_logs)
        self.validate_timelogs(self.user3, expected_time_logs)

    def get_http_user_url_from_api_response(self, user_response):
        return re.sub(".*/api/users", "/user", user_response['url'])

    def test_get_users(self):
        list_of_users = CustomUser.objects.all()
        response = self.client.get(reverse('api:customuser-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # even user that are not part of the same project are shown in the list
        # compare the amount
        self.assertEqual(response.json()['count'], len(list_of_users))
        responded_user = response.json()['results']
        # compare the names and url
        for i in range(len(responded_user)):
            # username
            self.assertEqual(responded_user[i]['username'], list_of_users[i].username)
            # url
            self.assertEqual(self.get_http_user_url_from_api_response(responded_user[i]),
                             list_of_users[i].get_absolute_url())

    def test_get_users_detail(self):
        response = self.client.get(reverse('api:customuser-detail', kwargs={'username': self.user1.username}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # username
        self.assertEqual(response.json()['username'], self.user1.username)
        # url
        self.assertEqual(self.get_http_user_url_from_api_response(response.json()), self.user1.get_absolute_url())

    # for each project in the lists compare
    # the lists of managers, developers, the url, name and short name with the data from the response
    # \param expected_proj_list the projects expected to be in the list - should be a list
    # \param proj_list_responded the response from an api project detail call
    #                            may not be a list when it contains only one project
    # \param num_proj_responded for this exact case there is a count parameter which should be 1 in that case
    def validate_project_details(self, expected_proj_list, proj_list_responded, count):
        # works even when proj_list_responded is not a list
        self.assertEqual(count, len(expected_proj_list))
        for i in range(len(expected_proj_list)):
            # avoid getting key errors (when there is only one project in the response there is no list)
            if type(proj_list_responded) == list:
                current_proj_responded = proj_list_responded[i]
            else:
                current_proj_responded = proj_list_responded
            # manager
            list_of_manager = expected_proj_list[i].manager.all()
            for j in range(len(list_of_manager)):
                self.assertEqual(current_proj_responded['manager'][j], list_of_manager[j].username)

            # developer
            list_of_developer = expected_proj_list[i].developer.all()
            for j in range(len(list_of_developer)):
                self.assertEqual(current_proj_responded['developer'][j], list_of_developer[j].username)

            # url
            responded_url = re.sub(".*/api/projects", "/project", current_proj_responded['url'])
            expected_url = re.sub("detail", "", expected_proj_list[i].get_absolute_url())
            self.assertEqual(responded_url, expected_url)
            # name
            self.assertEqual(current_proj_responded['name'], expected_proj_list[i].name)
            # name_short
            self.assertEqual(current_proj_responded['name_short'], expected_proj_list[i].name_short)

    def test_post_project(self):
        response = self.client.get(reverse('api:project-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        expected_proj_list = [self.project]
        self.validate_project_details(expected_proj_list, response.json()['results'], response.json()['count'])
        project_new_name = 'yoflow'
        project_data = {
                'name': project_new_name,
                'name_short': 'nanu'
                }
        # this creates a new project
        response = self.client.post(reverse('api:project-list'), project_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        # there are two projects now
        response = self.client.get(reverse('api:project-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        expected_proj_list = Project.objects.all()
        self.validate_project_details(expected_proj_list, response.json()['results'], response.json()['count'])

    def test_get_project_detail(self):
        response = self.client.get(reverse('api:project-detail', kwargs=self.short_name_kwargs))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.validate_project_details([self.project], response.json(), 1)

    def test_patch_project_detail(self):
        new_project_name = 'changing the project name'
        project_data = {
                'name': new_project_name,
                }
        # changes the name of the project
        response = self.client.patch(reverse('api:project-detail', kwargs=self.short_name_kwargs),
                                     data=project_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # get the project list to get the updated project data - self.project is outdated
        expected_proj_list = Project.objects.all()
        self.assertEqual(response.json()['name'], new_project_name)
        # check that the correct project was modified
        self.assertEqual(response.json()['name_short'], self.project.name_short)
        # compare api response with internal data
        self.validate_project_details([expected_proj_list[0]], response.json(), 1)

    def test_patch_project_detail_cant_remove_manager(self):
        project_data = {'manager': []}
        response = self.client.patch(reverse('api:project-detail', kwargs=self.short_name_kwargs),
                                     data=project_data,
                                     format='json')
        # patch should have failed since every project requires at least one project manager
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertNotEqual(len(Project.objects.filter(name_short=self.project.name_short)[0].manager.all()), 0)

    def test_put_project_detail(self):
        project_data = {
                'manager': ['user1'],
                'name': 'yoflow',
                }
        response = self.client.put(reverse('api:project-detail', kwargs=self.short_name_kwargs),
                                   data=project_data,
                                   format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()['name'], 'yoflow')
        self.assertEqual(response.json()['manager'], ['user1'])
        expected_proj_list = Project.objects.all()
        # compare api response with internal data
        self.validate_project_details([expected_proj_list[0]], response.json(), 1)

    # test deletes a project
    def test_delete_project_detail(self):
        # create a new project first to double check that only the selected project gets deleted
        new_project = Project(creator=self.user3, name_short='fooo', name="second project")
        new_project.save()
        # Either get this as a list - or call bool on expected_proj_list.
        # Otherwise the ProjectQuerySet is going to be evaluated once more (and hence updates the results)
        expected_proj_list = list(Project.objects.all()[1:])
        response = self.client.delete(reverse('api:project-detail', kwargs=self.short_name_kwargs))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        proj_list_post = list(Project.objects.all())
        self.assertEqual(proj_list_post, expected_proj_list)

    def test_get_project_issues(self):
        response = self.client.get(reverse('api:project_issues-list', kwargs=self.project_name_kwargs))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()['count'], len(Issue.objects.filter(project=self.project)))
        self.compare_issue_lists(response.json()['results'], list(Issue.objects.filter(project=self.project)))

        # create a new project user1 has no access to and get the list
        new_project_name_short = "newp"
        new_project_name = "new project"
        new_project = Project(creator=self.user3, name_short=new_project_name_short, name=new_project_name)
        new_project.save()
        new_project.manager.add(self.user3)
        new_project.developer.add(self.user3)
        new_issue = Issue(title='new issue for new project', project=new_project)
        new_issue.save()
        # user 1 has no access
        response = self.client.get(reverse('api:project_issues-list', kwargs={'project': new_project_name_short}))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # but user3 has
        self.use_user(self.user3)
        response = self.client.get(reverse('api:project_issues-list', kwargs={'project': new_project_name_short}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()['count'], len(Issue.objects.filter(project=new_project)))
        self.compare_issue_lists(response.json()['results'], list(Issue.objects.filter(project=new_project)))

    def test_post_project_issues(self):
        amount_of_issues_pre = len(Issue.objects.filter(project=self.project))
        issue_data = {
                'title': 'this is a issue',
                }
        response = self.client.post(reverse('api:project_issues-list', kwargs=self.project_name_kwargs),
                                    data=issue_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        # test that the new issue is part of the project
        self.assertContains(response, issue_data['title'], status_code=201)
        # test that there is an additional issue
        amount_of_issues_post = len(Issue.objects.filter(project=self.project))
        self.assertEqual(amount_of_issues_post, amount_of_issues_pre+1)

    def test_get_project_timelogs(self):
        # ############################## Testcase preparations
        # add new user as developer to project
        new_user = get_user_model().objects.create_user('user4', 'newuser', 'c')
        new_user.save()
        self.project.developer.add(new_user)
        # add timelog for new user - this should be visible by the new user and the manager
        new_log = Timelog(time=datetime.timedelta(hours=3), user=new_user, issue=self.issue)
        new_log.save()
        # new project and timelog for user2
        new_project_name_short = "newp"
        new_project_name = "new project"
        new_project = Project(creator=self.user2, name_short=new_project_name_short, name=new_project_name)
        new_project.save()
        new_project.manager.add(self.user2)
        new_issue = Issue(title='new issue of new proj', project=new_project)
        new_issue.save()
        # this timelog should not be visible in the current project self.project
        new_log_new_proj = Timelog(time=datetime.timedelta(hours=4), user=self.user2, issue=new_issue)
        new_log_new_proj.save()
        # ############################## Testcase start

        # user1 sees all timelogs of the project since they are manager
        response = self.client.get(reverse('api:project_timelogs-list', kwargs=self.project_name_kwargs))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # get timelogs of user1 and new_user which are the only ones that have times logged on this project
        timelogs_of_proj = list(Timelog.objects.filter(Q(user=self.user1) | Q(user=new_user)))
        amount_of_timelogs = len(timelogs_of_proj)
        self.assertEqual(response.json()['count'], amount_of_timelogs)
        self.compare_timelog_lists(response.json()['results'], timelogs_of_proj)

        # new user - that is only developer of this project and hence can't see the logs of user1
        self.use_user(new_user)
        response = self.client.get(reverse('api:project_timelogs-list', kwargs=self.project_name_kwargs))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        own_timelogs = list(Timelog.objects.filter(user=new_user))
        self.assertEqual(response.json()['count'], len(own_timelogs))
        self.compare_timelog_lists(response.json()['results'], own_timelogs)

        # user2 doesn't have timelogs on this project - only on other projects
        # also user2 is not a manager and hence shouldn't see any timelogs
        self.use_user(self.user2)
        response = self.client.get(reverse('api:project_timelogs-list', kwargs=self.project_name_kwargs))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()['count'], 0)

    # TODO TESTCASE test model data
    def test_get_project_issue_detail(self):
        response = self.client.get(reverse('api:project_issues-detail', kwargs=self.issue_number_kwargs))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response = self.client.get(reverse('api:project_issues-list', kwargs=self.project_name_kwargs))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    # TODO TESTCASE test model data
    def test_get_project_issue_detail(self):
        response = self.client.get(reverse('api:project_issues-detail', kwargs=self.issue_number_kwargs))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    # TODO TESTCASE test model data
    def test_put_project_issue_detail(self):
        issue_data = {
                'title': 'this is a issue',
                }
        response = self.client.put(reverse('api:project_issues-detail', kwargs=self.issue_number_kwargs),
                                   issue_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()['title'], 'this is a issue')

    # TODO TESTCASE test model data
    def test_patch_project_issue_detail(self):
        issue_data = {
                'title': 'this is a issue',
                }
        response = self.client.patch(reverse('api:project_issues-detail', kwargs=self.issue_number_kwargs),
                                     issue_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()['title'], 'this is a issue')

    # TODO TESTCASE test model data
    def test_delete_project_issue_detail(self):
        response = self.client.delete(reverse('api:project_issues-detail', kwargs=self.issue_number_kwargs))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    # TODO TESTCASE test model data
    def test_get_project_issue_comments(self):
        response = self.client.get(reverse('api:project_issues_comments-list', kwargs=self.issue_number2_kwargs))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    # TODO TESTCASE test model data
    def test_post_project_issue_comments(self):
        comment_data = {
                'text': 'good evening'
        }
        response = self.client.post(reverse('api:project_issues_comments-list', kwargs=self.issue_number2_kwargs),
                                    comment_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    # TODO TESTCASE test model data
    def test_get_project_issue_timelogs(self):
        response = self.client.get(reverse('api:project_issues_timelogs-list', kwargs=self.issue_number2_kwargs))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    # TODO TESTCASE test model data
    def test_post_project_issue_timelogs(self):
        timelog_data = {
                'time': '2h'
        }
        response = self.client.post(reverse('api:project_issues_timelogs-list', kwargs=self.issue_number2_kwargs),
                                    timelog_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    # TODO TESTCASE test model data
    def test_get_project_issue_comments_detail(self):
        response = self.client.get(reverse('api:project_issues_comments-detail', kwargs=self.comment_seqnum_kwargs))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    # TODO TESTCASE test model data
    def test_put_project_issue_comments_detail(self):
        comment_data = {
            'text': 'new content'
                }
        response = self.client.put(reverse('api:project_issues_comments-detail', kwargs=self.comment_seqnum_kwargs),
                                   comment_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()['text'], 'new content')

    # TODO TESTCASE test model data
    def test_patch_project_issue_comments_detail(self):
        comment_data = {
            'text': 'new content'
                }
        response = self.client.patch(reverse('api:project_issues_comments-detail', kwargs=self.comment_seqnum_kwargs),
                                     comment_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()['text'], 'new content')

    # TODO TESTCASE test model data
    def test_delete_project_issue_comments_detail(self):
        response = self.client.delete(reverse('api:project_issues_comments-detail', kwargs=self.comment_seqnum_kwargs))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    # TODO TESTCASE test model data
    def test_get_project_issue_timelogs_detail(self):
        response = self.client.get(reverse('api:project_issues_timelogs-detail', kwargs=self.timelog_number_kwargs))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    # TODO TESTCASE test model data
    def test_put_project_issue_timelogs_detail(self):
        log_data = {
                'time': '4h10m'
                }
        response = self.client.put(reverse('api:project_issues_timelogs-detail', kwargs=self.timelog_number_kwargs),
                                   log_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()['time'], '4h 10m')

    # TODO TESTCASE test model data
    def test_patch_project_issue_timelogs_detail(self):
        log_data = {
                'time': '4h10m'
                }
        response = self.client.patch(reverse('api:project_issues_timelogs-detail', kwargs=self.timelog_number_kwargs),
                                     log_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()['time'], '4h 10m')

    # TODO TESTCASE test model data
    def test_delete_project_issue_timelogs_detail(self):
        response = self.client.delete(reverse('api:project_issues_timelogs-detail', kwargs=self.timelog_number_kwargs))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

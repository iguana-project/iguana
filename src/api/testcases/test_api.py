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
from user_management.models import CustomUser
from django.contrib.auth import get_user_model
from django.db.models import Q

import base64
import json
import datetime


class ApiTest(APITestCase):
    @classmethod
    def setUpTestData(cls):
        # NOTE: if you modify these elements they need to be created in setUp(), instead of here
        cls.user1 = get_user_model().objects.create_user('user1', 'mail', 'c')
        cls.user2 = get_user_model().objects.create_user('user2', 'othermail', 'c')
        cls.user3 = get_user_model().objects.create_user('user3', 'foothermail', 'c')

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

    # change user and credentials used for api authorization
    def use_user(self, user_to_be_logged_in):
        # all user use 'c' as password
        self.client.credentials(HTTP_AUTHORIZATION='Basic ' +
                                base64.b64encode((str(user_to_be_logged_in)+':c').encode()).decode())

    # check whether the provided user is assigned to the expected amount of issues
    def validate_issues_assigned(self, user, list_of_issues):
        # use the provided user for the api request
        self.use_user(user)
        # check assignments on the model data
        self.assertEqual(list(Issue.objects.filter(assignee=user)), list_of_issues)

        # api response
        response = self.client.get(reverse('api:issues-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json().get('count'), len(list_of_issues))
        responded_list_of_issues = []
        name_list_of_issues = []
        # get the names of the expected issues and issues returned by the api
        for i in range(len(list_of_issues)):
            responded_list_of_issues += [response.json().get('results')[i]['title']]
            name_list_of_issues += [str(list_of_issues[i])]
        # compare the two issue name lists
        self.assertEqual(responded_list_of_issues, name_list_of_issues)

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

    def validate_projects_readable(self, user, expected_num_of_projects, list_of_projs):
        self.use_user(user)
        response = self.client.get(reverse('api:project-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json().get('count'), expected_num_of_projects)
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

    def test_get_timelogs(self):
        response = self.client.get(reverse('api:timelogs-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json().get('count'), 1)
        log = Timelog(issue=self.issue_new, user=self.user1, time=datetime.timedelta(hours=2))
        log.save()
        response = self.client.get(reverse('api:timelogs-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json().get('count'), 2)

    def test_get_users(self):
        response = self.client.get(reverse('api:customuser-list'))
        self.assertEqual(response.json().get('count'), len(CustomUser.objects.all()))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_users_detail(self):
        response = self.client.get(reverse('api:customuser-detail', kwargs={'username': self.user1.username}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn(self.user1.username, response.json().get('username'))

    def test_post_project(self):
        project_data = {
                'name': 'yoflow',
                'name_short': 'nanu'
                }
        response = self.client.post(reverse('api:project-list'), project_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        response = self.client.get(reverse('api:project-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json().get('count'), 2)

    def test_get_project_detail(self):
        response = self.client.get(reverse('api:project-detail', kwargs={'name_short': self.project.name_short}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_patch_project_detail(self):
        project_data = {
                'name': 'yoflow',
                }
        response = self.client.patch(reverse('api:project-detail', kwargs={'name_short': self.project.name_short}),
                                     data=project_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json().get('name'), 'yoflow')
        self.assertEqual(response.json().get('name_short'), self.project.name_short)

        # assert - at least one project manager
        project_data.update({'manager': [], 'developer': []})
        response = self.client.patch(reverse('api:project-detail', kwargs={'name_short': self.project.name_short}),
                                     data=project_data,
                                     format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_put_project_detail(self):
        project_data = {
                'manager': ['user1'],
                'name': 'yoflow',
                }
        response = self.client.put(reverse('api:project-detail', kwargs={'name_short': self.project.name_short}),
                                   data=project_data,
                                   format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json().get('name'), 'yoflow')

    def test_delete_project_detail(self):
        response = self.client.delete(reverse('api:project-detail', kwargs={'name_short': self.project.name_short}))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_get_project_issues(self):
        response = self.client.get(reverse('api:project_issues-list', kwargs={'project': self.project.name_short}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_post_project_issues(self):
        issue_data = {
                'title': 'this is a issue',
                }
        response = self.client.post(reverse('api:project_issues-list', kwargs={'project': self.project.name_short}),
                                    data=issue_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_get_project_timelogs(self):
        response = self.client.get(reverse('api:project_timelogs-list', kwargs={'project': self.project.name_short}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_project_issue_detail(self):
        response = self.client.get(reverse('api:project_issues-detail',
                                           kwargs={'project': self.project.name_short, 'number': self.issue.number}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response = self.client.get(reverse('api:project_issues-list', kwargs={'project': self.project.name_short}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_project_timelogs(self):
        response = self.client.get(reverse('api:project_timelogs-list', kwargs={'project': self.project.name_short}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_project_issue_detail(self):
        response = self.client.get(reverse('api:project_issues-detail',
                                           kwargs={'project': self.project.name_short, 'number': self.issue.number}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_put_project_issue_detail(self):
        issue_data = {
                'title': 'this is a issue',
                }
        response = self.client.put(reverse('api:project_issues-detail',
                                           kwargs={'project': self.project.name_short, 'number': self.issue.number}),
                                   issue_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json().get('title'), 'this is a issue')

    def test_patch_project_issue_detail(self):
        issue_data = {
                'title': 'this is a issue',
                }
        response = self.client.patch(reverse('api:project_issues-detail',
                                             kwargs={'project': self.project.name_short, 'number': self.issue.number}),
                                     issue_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json().get('title'), 'this is a issue')

    def test_delete_project_issue_detail(self):
        response = self.client.delete(reverse('api:project_issues-detail',
                                              kwargs={'project': self.project.name_short, 'number': self.issue.number}))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_get_project_issue_comments(self):
        response = self.client.get(reverse('api:project_issues_comments-list',
                                           kwargs={'project': self.project.name_short, 'issue': self.issue.number}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_post_project_issue_comments(self):
        comment_data = {
                'text': 'good evening'
        }
        response = self.client.post(reverse('api:project_issues_comments-list',
                                            kwargs={'project': self.project.name_short, 'issue': self.issue.number}),
                                    comment_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_get_project_issue_timelogs(self):
        response = self.client.get(reverse('api:project_issues_timelogs-list',
                                           kwargs={'project': self.project.name_short, 'issue': self.issue.number}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_post_project_issue_timelogs(self):
        timelog_data = {
                'time': '2h'
        }
        response = self.client.post(reverse('api:project_issues_timelogs-list',
                                            kwargs={'project': self.project.name_short, 'issue': self.issue.number}),
                                    timelog_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_get_project_issue_comments_detail(self):
        response = self.client.get(reverse('api:project_issues_comments-detail',
                                           kwargs={'project': self.project.name_short,
                                                   'issue': self.issue.number,
                                                   'seqnum': self.comment.seqnum}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_put_project_issue_comments_detail(self):
        comment_data = {
            'text': 'new content'
                }
        response = self.client.put(reverse('api:project_issues_comments-detail',
                                           kwargs={'project': self.project.name_short,
                                                   'issue': self.issue.number,
                                                   'seqnum': self.comment.seqnum}),
                                   comment_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json().get('text'), 'new content')

    def test_patch_project_issue_comments_detail(self):
        comment_data = {
            'text': 'new content'
                }
        response = self.client.patch(reverse('api:project_issues_comments-detail',
                                             kwargs={'project': self.project.name_short,
                                                     'issue': self.issue.number,
                                                     'seqnum': self.comment.seqnum}),
                                     comment_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json().get('text'), 'new content')

    def test_delete_project_issue_comments_detail(self):
        response = self.client.delete(reverse('api:project_issues_comments-detail',
                                              kwargs={'project': self.project.name_short,
                                                      'issue': self.issue.number,
                                                      'seqnum': self.comment.seqnum}))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_get_project_issue_timelogs_detail(self):
        response = self.client.get(reverse('api:project_issues_timelogs-detail',
                                           kwargs={'project': self.project.name_short,
                                                   'issue': self.issue.number,
                                                   'number': self.log.number}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_put_project_issue_timelogs_detail(self):
        log_data = {
                'time': '4h10m'
                }
        response = self.client.put(reverse('api:project_issues_timelogs-detail',
                                           kwargs={'project': self.project.name_short,
                                                   'issue': self.issue.number,
                                                   'number': self.log.number}),
                                   log_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json().get('time'), '4h 10m')

    def test_patch_project_issue_timelogs_detail(self):
        log_data = {
                'time': '4h10m'
                }
        response = self.client.patch(reverse('api:project_issues_timelogs-detail',
                                             kwargs={'project': self.project.name_short,
                                                     'issue': self.issue.number,
                                                     'number': self.log.number}),
                                     log_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json().get('time'), '4h 10m')

    def test_delete_project_issue_timelogs_detail(self):
        response = self.client.delete(reverse('api:project_issues_timelogs-detail',
                                              kwargs={'project': self.project.name_short,
                                                      'issue': self.issue.number,
                                                      'number': self.log.number}))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

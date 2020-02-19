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

from project.models import Project
from issue.models import Issue, Comment
from timelog.models import Timelog
from django.contrib.auth import get_user_model

import base64
import json
import datetime


class ApiTest(APITestCase):
    @classmethod
    def setUpTestData(cls):
        # NOTE: if you modify these elements they need to be created in setUp(), instead of here
        cls.user1 = get_user_model().objects.create_user('user1', 'mail', 'c')
        cls.user2 = get_user_model().objects.create_user('user2', 'othermail', 'c')

    def setUp(self):
        # NOTE: these elements get modified by some testcases, so they should NOT be created in setUpTestData()
        self.project = Project(creator=self.user1, name_short='asdf')
        self.project.save()
        self.project.developer.add(self.user1)
        self.project.developer.add(self.user2)
        self.project.manager.add(self.user1)
        self.issue = Issue(title='test', project=self.project)
        self.issue.save()
        self.comment = Comment(text='test', creator=self.user1, issue=self.issue)
        self.comment.save()
        self.log = Timelog(time=datetime.timedelta(hours=2), user=self.user1, issue=self.issue)
        self.log.save()
        self.client.credentials(HTTP_AUTHORIZATION='Basic ' + base64.b64encode('user1:c'.encode()).decode())

    def test_get_issues(self):
        response = self.client.get(reverse('api:issues-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json().get('count'), 0)
        issue = Issue(title='asdf', project=self.project)
        issue.save()
        issue.assignee.add(self.user1)
        response = self.client.get(reverse('api:issues-list'))
        self.assertEqual(response.json().get('count'), 1)
        issue = Issue(title='asdf2', project=self.project)
        issue.save()
        issue.assignee.add(self.user2)
        response = self.client.get(reverse('api:issues-list'))
        self.assertEqual(response.json().get('count'), 1)

    def test_get_projects(self):
        response = self.client.get(reverse('api:project-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json().get('count'), 1)

    def test_get_timelogs(self):
        response = self.client.get(reverse('api:timelogs-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json().get('count'), 1)
        issue = Issue(title='asdf', project=self.project)
        issue.save()
        log = Timelog(issue=issue, user=self.user1, time=datetime.timedelta(hours=2))
        log.save()
        response = self.client.get(reverse('api:timelogs-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json().get('count'), 2)

    def test_get_users(self):
        response = self.client.get(reverse('api:customuser-list'))
        self.assertEqual(response.json().get('count'), 2)
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
        self.assertEqual(response.json().get('name_short'), 'asdf')

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

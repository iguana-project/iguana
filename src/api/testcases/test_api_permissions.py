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


class ApiPermissionTest(APITestCase):
    @classmethod
    def setUpTestData(cls):
        # NOTE: if you modify those elements they need to be created in setUp(), instead of here
        cls.user1 = get_user_model().objects.create_user('user1', 'mail', 'c')
        cls.user2 = get_user_model().objects.create_user('user2', 'othermail', 'c')

    def setUp(self):
        # NOTE: these elements get modified by some testcases, so they should NOT be created in setUpTestData()
        self.project = Project(creator=self.user1, name_short='asdf')
        self.project.save()
        self.project.developer.add(self.user1)
        self.project.developer.add(self.user2)
        self.project.manager.add(self.user1)
        self.project2 = Project(creator=self.user2, name_short='asdg')
        self.project2.save()
        self.project2.manager.add(self.user2)
        self.issue = Issue(title='test', project=self.project)
        self.issue.save()
        self.issue2 = Issue(title='test', project=self.project2)
        self.issue2.save()
        self.comment = Comment(text='test', creator=self.user1, issue=self.issue)
        self.comment.save()
        self.comment2 = Comment(text='test', creator=self.user2, issue=self.issue2)
        self.comment2.save()
        self.log = Timelog(time=datetime.timedelta(hours=2), user=self.user1, issue=self.issue)
        self.log.save()
        self.log2 = Timelog(time=datetime.timedelta(hours=2), user=self.user2, issue=self.issue2)
        self.log2.save()
        self.user1_auth = 'Basic ' + base64.b64encode('user1:c'.encode()).decode()
        self.user2_auth = 'Basic ' + base64.b64encode('user2:c'.encode()).decode()
        self.client.credentials(HTTP_AUTHORIZATION=self.user1_auth)

    def try_project_put_patch_delete(self, expected):
        project_data = {
            'name': 'yoflow',
        }
        response = self.client.patch(reverse('api:project-detail', kwargs={'name_short': self.project.name_short}),
                                     data=project_data)
        self.assertEqual(response.status_code, expected)
        response = self.client.put(reverse('api:project-detail', kwargs={'name_short': self.project.name_short}),
                                   data=project_data)
        self.assertEqual(response.status_code, expected)
        response = self.client.delete(reverse('api:project-detail', kwargs={'name_short': self.project.name_short}))
        self.assertEqual(response.status_code, expected)

    def test_project_permissions(self):
        # project1 granted
        response = self.client.get(reverse('api:project-detail', kwargs={'name_short': self.project.name_short}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # project2 denied for user1
        response = self.client.get(reverse('api:project-detail', kwargs={'name_short': self.project2.name_short}))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        # project2 granted for user2
        self.client.credentials(HTTP_AUTHORIZATION=self.user2_auth)
        response = self.client.get(reverse('api:project-detail', kwargs={'name_short': self.project2.name_short}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # project1 user2 put, patch, delete denied (no manager)
        self.try_project_put_patch_delete(status.HTTP_403_FORBIDDEN)

        # no credentials
        self.client.credentials()
        self.try_project_put_patch_delete(status.HTTP_401_UNAUTHORIZED)

    def test_project_issues_get_post_permissions(self):
        issue_data = {
                'title': 'laalalla'
                }
        # project1 granted
        response = self.client.get(reverse('api:project_issues-list', kwargs={'project': self.project.name_short}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response = self.client.post(reverse('api:project_issues-list', kwargs={'project': self.project.name_short}),
                                    issue_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        # project2 denied for user1
        response = self.client.get(reverse('api:project_issues-list', kwargs={'project': self.project2.name_short}))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        response = self.client.post(reverse('api:project_issues-list', kwargs={'project': self.project2.name_short}),
                                    issue_data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        # project2 granted for user2
        self.client.credentials(HTTP_AUTHORIZATION=self.user2_auth)
        response = self.client.get(reverse('api:project_issues-list', kwargs={'project': self.project2.name_short}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response = self.client.post(reverse('api:project_issues-list', kwargs={'project': self.project2.name_short}),
                                    issue_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # no credentials
        self.client.credentials()
        response = self.client.get(reverse('api:project_issues-list', kwargs={'project': self.project2.name_short}))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        response = self.client.post(reverse('api:project_issues-list', kwargs={'project': self.project2.name_short}),
                                    issue_data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def try_issue_put_patch_delete(self, expected):
        issue_data = {
            'title': 'yoflow',
        }
        url = 'api:project_issues-detail'
        response = self.client.get(reverse(url, kwargs={'project': self.project2.name_short,
                                                        'number': self.issue2.number}))
        self.assertIn(response.status_code, expected)
        response = self.client.patch(reverse(url, kwargs={'project': self.project2.name_short,
                                                          'number': self.issue2.number}),
                                     data=issue_data)
        self.assertIn(response.status_code, expected)
        response = self.client.put(reverse(url, kwargs={'project': self.project2.name_short,
                                                        'number': self.issue2.number}),
                                   data=issue_data)
        self.assertIn(response.status_code, expected)
        response = self.client.delete(reverse(url, kwargs={'project': self.project2.name_short,
                                                           'number': self.issue2.number}))
        self.assertIn(response.status_code, expected)

    def test_project_issues_detail_put_patch_delete_permissions(self):

        # user1 not in project1
        self.try_issue_put_patch_delete([status.HTTP_403_FORBIDDEN])

        # user2 in project2
        self.client.credentials(HTTP_AUTHORIZATION=self.user2_auth)
        self.try_issue_put_patch_delete([status.HTTP_200_OK, status.HTTP_204_NO_CONTENT])

        # not credentials
        self.client.credentials()
        self.try_issue_put_patch_delete([status.HTTP_401_UNAUTHORIZED])

    def test_project_issue_comments_get_post_permissions(self):
        comment_data = {
                'text': 'laalalla'
                }
        # project1 granted
        response = self.client.get(reverse('api:project_issues_comments-list',
                                           kwargs={'project': self.project.name_short, 'issue': self.issue.number}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response = self.client.post(reverse('api:project_issues_comments-list',
                                            kwargs={'project': self.project.name_short, 'issue': self.issue.number}),
                                    comment_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        # project2 denied for user1
        response = self.client.get(reverse('api:project_issues_comments-list',
                                           kwargs={'project': self.project2.name_short, 'issue': self.issue2.number}))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        response = self.client.post(reverse('api:project_issues_comments-list',
                                            kwargs={'project': self.project2.name_short, 'issue': self.issue2.number}),
                                    comment_data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        # project2 granted for user2
        self.client.credentials(HTTP_AUTHORIZATION=self.user2_auth)
        response = self.client.get(reverse('api:project_issues_comments-list',
                                           kwargs={'project': self.project2.name_short, 'issue': self.issue2.number}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response = self.client.post(reverse('api:project_issues_comments-list',
                                            kwargs={'project': self.project2.name_short, 'issue': self.issue2.number}),
                                    comment_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # no credentials
        self.client.credentials()
        response = self.client.get(reverse('api:project_issues_comments-list',
                                           kwargs={'project': self.project2.name_short, 'issue': self.issue2.number}))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        response = self.client.post(reverse('api:project_issues_comments-list',
                                            kwargs={'project': self.project2.name_short, 'issue': self.issue2.number}),
                                    comment_data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def try_issue_comments_put_patch_delete(self, expected):
        comment_data = {
            'text': 'lalala',
        }
        url = 'api:project_issues_comments-detail'
        response = self.client.get(reverse(url, kwargs={'project': self.project2.name_short,
                                                        'issue': self.issue2.number,
                                                        'seqnum': self.comment2.seqnum}))
        self.assertIn(response.status_code, expected)
        response = self.client.patch(reverse(url, kwargs={'project': self.project2.name_short,
                                                          'issue': self.issue2.number,
                                                          'seqnum': self.comment2.seqnum}),
                                     data=comment_data)
        self.assertIn(response.status_code, expected)
        response = self.client.put(reverse(url, kwargs={'project': self.project2.name_short,
                                                        'issue': self.issue2.number,
                                                        'seqnum': self.comment2.seqnum}),
                                   data=comment_data)
        self.assertIn(response.status_code, expected)
        response = self.client.delete(reverse(url, kwargs={'project': self.project2.name_short,
                                                           'issue': self.issue2.number,
                                                           'seqnum': self.comment2.seqnum}))
        self.assertIn(response.status_code, expected)

    def test_project_issues_comments_detail_put_patch_delete_permissions(self):
        # TODO TESTCASE difference manager/not manager

        # user1 not in project1
        self.try_issue_comments_put_patch_delete([status.HTTP_403_FORBIDDEN])

        self.client.credentials(HTTP_AUTHORIZATION=self.user2_auth)
        # user2 in project2
        self.try_issue_comments_put_patch_delete([status.HTTP_200_OK, status.HTTP_204_NO_CONTENT])
        self.client.credentials()
        self.try_issue_comments_put_patch_delete([status.HTTP_401_UNAUTHORIZED])

    def test_project_issue_timelogs_get_post_permissions(self):
        log_data = {
                'time': '2h5m'
                }
        # project1 granted
        response = self.client.get(reverse('api:project_issues_timelogs-list',
                                           kwargs={'project': self.project.name_short, 'issue': self.issue.number}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response = self.client.post(reverse('api:project_issues_timelogs-list',
                                            kwargs={'project': self.project.name_short, 'issue': self.issue.number}),
                                    log_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        # project2 denied for user1
        response = self.client.get(reverse('api:project_issues_timelogs-list',
                                           kwargs={'project': self.project2.name_short, 'issue': self.issue2.number}))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        response = self.client.post(reverse('api:project_issues_timelogs-list',
                                            kwargs={'project': self.project2.name_short, 'issue': self.issue2.number}),
                                    log_data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        # project2 granted for user2
        self.client.credentials(HTTP_AUTHORIZATION=self.user2_auth)
        response = self.client.get(reverse('api:project_issues_timelogs-list',
                                           kwargs={'project': self.project2.name_short, 'issue': self.issue2.number}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response = self.client.post(reverse('api:project_issues_timelogs-list',
                                            kwargs={'project': self.project2.name_short, 'issue': self.issue2.number}),
                                    log_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # no credentials
        self.client.credentials()
        response = self.client.get(reverse('api:project_issues_timelogs-list',
                                           kwargs={'project': self.project2.name_short, 'issue': self.issue2.number}))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        response = self.client.post(reverse('api:project_issues_timelogs-list',
                                            kwargs={'project': self.project2.name_short, 'issue': self.issue2.number}),
                                    log_data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    # helper function
    def try_issue_timelogs_put_patch_delete(self, expected):
        log_data = {
            'time': '2h5m'
        }
        url = 'api:project_issues_timelogs-detail'
        response = self.client.get(reverse(url, kwargs={'project': self.project2.name_short,
                                                        'issue': self.issue2.number,
                                                        'number': self.log2.number}))
        self.assertIn(response.status_code, expected)
        response = self.client.patch(reverse(url, kwargs={'project': self.project2.name_short,
                                                          'issue': self.issue2.number,
                                                          'number': self.log2.number}),
                                     data=log_data)
        self.assertIn(response.status_code, expected)
        response = self.client.put(reverse(url, kwargs={'project': self.project2.name_short,
                                                        'issue': self.issue2.number,
                                                        'number': self.log2.number}),
                                   data=log_data)
        self.assertIn(response.status_code, expected)
        response = self.client.delete(reverse(url, kwargs={'project': self.project2.name_short,
                                                           'issue': self.issue2.number,
                                                           'number': self.log2.number}))
        self.assertIn(response.status_code, expected)

    def test_project_issues_timelogs_detail_put_patch_delete_permissions(self):
        # TODO TESTCASE difference manager/not manager
        # user1 not in project1
        self.try_issue_timelogs_put_patch_delete([status.HTTP_403_FORBIDDEN])

        self.client.credentials(HTTP_AUTHORIZATION=self.user2_auth)
        # user2 in project2
        self.try_issue_timelogs_put_patch_delete([status.HTTP_200_OK, status.HTTP_204_NO_CONTENT])
        self.client.credentials()
        self.try_issue_timelogs_put_patch_delete([status.HTTP_401_UNAUTHORIZED])

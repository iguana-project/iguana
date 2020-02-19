"""
Iguana (c) by Marc Ammon, Moritz Fickenscher, Lukas Fridolin,
Michael Gunselmann, Katrin Raab, Christian Strate

Iguana is licensed under a
Creative Commons Attribution-ShareAlike 4.0 International License.

You should have received a copy of the license along with this
work. If not, see <http://creativecommons.org/licenses/by-sa/4.0/>.
"""
import tempfile
from os import path
import os

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta

from issue.views import IssueEditCommentView
from user_management.views import LoginView
from project.models import Project
from kanbancol.models import KanbanColumn
from issue.models import Issue, Comment
from django.contrib.auth import get_user_model

from common.settings import MEDIA_ROOT
from common.testcases.generic_testcase_helper import view_and_template, redirect_to_login_and_login_required


class CommentTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        # NOTE: if you modify these elements they need to be created in setUp(), instead of here
        cls.user = get_user_model().objects.create_user('lalala', 'b', 'c')
        cls.user2 = get_user_model().objects.create_user('lululu', 'e', 'f')

    def setUp(self):
        self.client.force_login(self.user)
        # NOTE: these elements get modified by some testcases, so they should NOT be created in setUpTestData()
        self.project = Project(creator=self.user, name_short='PRJ')
        self.project.save()
        self.project.manager.add(self.user)
        self.project.developer.add(self.user)
        self.column = KanbanColumn(name='Column', position=4, project=self.project)
        self.column.save()
        self.issue = Issue(title="Test-Issue", project=self.project, kanbancol=self.column, type="Bug")
        self.issue.save()

    def test_view_and_template(self):
        # create comment
        comment = Comment(text="comment text", creator=self.user, issue=self.issue)
        comment.save()

        # edit comment-view
        view_and_template(self, IssueEditCommentView, 'comment/comment_edit.html', 'issue:edit_comment',
                          address_kwargs={'project': self.project.name_short, 'sqn_i': 1, 'pk_c': 1},
                          get_kwargs={'text': "comment text"})

        # TODO TESTCASE issue:delete_comment

    def test_redirect_to_login_and_login_required(self):
        # create comment + logout
        comment = Comment(text="comment text", creator=self.user, issue=self.issue)
        comment.save()
        self.client.logout()

        # edit comment-view
        redirect_to_login_and_login_required(self, 'issue:edit_comment',
                                             address_kwargs={'project': self.project.name_short, 'sqn_i': 1, 'pk_c': 1})

        # TODO TESTCASE issue:delete_comment

    def test_user_passes_test_mixin(self):
        proj_name2 = "project"
        proj_short2 = "cccc"
        project2 = Project(name=proj_name2, name_short=proj_short2, creator=self.user)
        project2.save()
        issue = Issue(title="p1-iss", project=self.project)
        issue.save()
        issue2 = Issue(title="p2-iss", project=project2)
        issue2.save()
        comment_text = "Fancy comment text"
        comment_edit = "EDITED AND CHANGED COMMENT"
        new_comment = {
            'action': "commentAtt",
            'text': comment_text
        }
        edit_comment = {
            'text': comment_edit
        }
        comment1 = Comment(creator=self.user, issue=issue, text=comment_text)
        comment1.save()
        comment2 = Comment(creator=self.user, issue=issue2, text=comment_text)
        comment2.save()

        self.client.logout()
        self.client.force_login(self.user2)

        # developer is good
        self.project.developer.add(self.user2)
        self.project.save()
        # create
        response = self.client.post(reverse('issue:detail',
                                            kwargs={'project': self.project.name_short, 'sqn_i': issue.number}),
                                    new_comment, follow=True)
        self.assertNotContains(response, "Your account doesn't have access to this page. To proceed, please " +
                                         "login with an account that has access.")
        self.assertEqual(issue.comments.count(), 2)
        # edit
        # developer can edit only their own comments
        response = self.client.post(reverse('issue:edit_comment',
                                    kwargs={'project': self.project.name_short, 'sqn_i': issue.number, 'pk_c': 2}),
                                    edit_comment, follow=True)
        self.assertNotContains(response, "Your account doesn't have access to this page. To proceed, please " +
                                         "login with an account that has access.")
        self.assertEqual(issue.comments.count(), 2)
        self.assertEqual(issue.comments.get(seqnum=2).text, comment_edit)

        # manager is good
        project2.manager.add(self.user2)
        project2.save()
        # create
        response = self.client.post(reverse('issue:detail',
                                            kwargs={'project': proj_short2, 'sqn_i': 1}),
                                    new_comment, follow=True)
        self.assertNotContains(response, "Your account doesn't have access to this page. To proceed, please " +
                                         "login with an account that has access.")
        self.assertEqual(issue2.comments.count(), 2)
        # edit
        # even manager can edit only their own comments
        response = self.client.post(reverse('issue:edit_comment',
                                    kwargs={'project': proj_short2, 'sqn_i': 1, 'pk_c': 2}),  # TODO pkc=1 probieren s.o
                                    edit_comment, follow=True)
        self.assertNotContains(response, "Your account doesn't have access to this page. To proceed, please " +
                                         "login with an account that has access.")
        self.assertEqual(issue2.comments.count(), 2)
        self.assertEqual(issue2.comments.get(seqnum=2).text, comment_edit)

    def test_comments_from_other_issues_of_same_project_invisible(self):
        # TODO TESTCASE
        pass

    def test_create_and_edit_comments_with_get_requests_disabled(self):
        # TODO TESTCASE
        pass

    def test_comment_create(self):
        comment_text = "Fancy comment text"
        comment1 = Comment(creator=self.user, issue=self.issue, text=comment_text)
        comment1.save()

        self.assertEqual(Issue.objects.count(), 1)
        self.assertEqual(self.issue.comments.count(), 1)
        self.assertEqual(self.issue.comments.first().text, comment_text)

    def test_comment_delete(self):
        # create sample issue
        issue = Issue(title="Test-Issue", project=self.project, kanbancol=self.column, type="Bug")
        issue.save()
        # create sample comment
        comment = Comment(text="Test Comment", creator=self.user, issue=issue)
        comment.save()

        # delete the comment
        response = self.client.get(reverse('issue:delete_comment',
                                           kwargs={'project': self.project.name_short,
                                                   'sqn_i': issue.number,
                                                   'pk_c': comment.pk}),
                                   follow=True)
        self.assertRedirects(response, reverse('issue:detail', kwargs={'project': self.project.name_short,
                                                                       'sqn_i': issue.number}))
        self.assertFalse(issue.comments.all().exists())

    def test_comment_edit(self):
        # TODO TESTCASE
        pass

    def test_comment_seqnum_stays_after_editing(self):
        self.assertEqual(self.issue.nextCommentId, 1)

        values = {
            'text': "comment text"
        }

        # create comment + logout
        comment = Comment(text=values['text'], creator=self.user, issue=self.issue)
        comment.save()

        issue = Issue.objects.get(pk=self.issue.pk)
        self.assertEqual(Comment.objects.count(), 1)
        self.assertEqual(Comment.objects.first().seqnum, 1)
        self.assertEqual(issue.comments.count(), 1)
        comment = issue.comments.first()
        self.assertEqual(comment.text, values['text'])
        self.assertEqual(issue.nextCommentId, 2)

        # check creator and time
        self.assertEqual(comment.creator, self.user)
        self.assertLess(comment.when, timezone.now())
        self.assertGreater(comment.when, timezone.now() - timedelta(seconds=10))

        values['text'] = "new comment text"

        # edit comment and assert that seqnum stays the same
        response = self.client.post(reverse('issue:edit_comment',
                                    kwargs={'project': self.project.name_short, 'sqn_i': 1, 'pk_c': comment.seqnum}),
                                    values)
        self.assertRedirects(response,
                             reverse('issue:detail',
                                     kwargs={'project': self.project.name_short, 'sqn_i': 1}
                                     )+'#comment1'
                             )
        response = self.client.get(response['location'])
        self.assertEqual(response.status_code, 200)

        issue = Issue.objects.get(pk=issue.pk)
        self.assertEqual(Comment.objects.count(), 1)
        self.assertEqual(Comment.objects.first().seqnum, 1)
        self.assertEqual(issue.comments.count(), 1)
        comment = issue.comments.first()
        self.assertEqual(comment.text, values['text'])
        self.assertEqual(issue.nextCommentId, 2)

    def test_comment_attach_log(self):
        # TODO TESTCASE move this test into an own class when splitting up the issue application
        # add a comment
        values = {
            'action': "commentAtt",  # the action is for the multiforms.py
            'text': "only a comment"
        }

        response = self.client.post(reverse('issue:detail',
                                            kwargs={'project': self.project.name_short, 'sqn_i': 1}),
                                    values, follow=True)
        self.assertContains(response, values['text'])

        # add comment and a file
        filecontent = 'Hello World'
        temp = tempfile.NamedTemporaryFile(delete=False)
        temp.write(filecontent.encode())
        temp.close()
        f = open(temp.name, 'r')

        values['text'] = "a comment with a file"
        values['file'] = f
        response = self.client.post(reverse('issue:detail',
                                            kwargs={'project': self.project.name_short, 'sqn_i': 1}),
                                    values, follow=True)
        self.assertContains(response, values['text'])
        for com in self.issue.comments.all():
            if com.attachment:
                self.assertEqual(path.basename(com.attachment.file.name), path.basename(temp.name))
                # deletion takes place below

        # add only a file
        del values['text']
        commentCount = len(self.issue.comments.all())
        response = self.client.post(reverse('issue:detail',
                                            kwargs={'project': self.project.name_short, 'sqn_i': 1}),
                                    values, follow=True)
        self.assertEqual(commentCount, len(self.issue.comments.all()))
        for form in response.context_data['forms'].values():
            self.assertFalse(form.is_valid())

        # close the file
        f.close()
        os.remove(temp.name)

        # add single file
        filecontent = 'Hello World'
        temp = tempfile.NamedTemporaryFile(delete=False)
        temp.write(filecontent.encode())
        temp.close()
        f = open(temp.name, 'r')

        values['action'] = "attachment"
        values['file'] = f
        response = self.client.post(reverse('issue:detail',
                                            kwargs={'project': self.project.name_short, 'sqn_i': 1}),
                                    values, follow=True)
        self.assertContains(response, path.basename(temp.name))

        # close the file
        f.close()
        # delete the uploaded file locally
        os.unlink(temp.name)

        # delete the uploaded files from the server
        for att in self.issue.attachments.all():
            os.unlink(MEDIA_ROOT + '/' + att.file.name)

        # add time log
        values['action'] = "timelog"
        del values['file']
        values['time'] = "1h"
        response = self.client.post(reverse('issue:detail',
                                            kwargs={'project': self.project.name_short, 'sqn_i': 1}),
                                    values, follow=True)
        self.assertContains(response, "1 Hour")

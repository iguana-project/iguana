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
import os
import tempfile

from issue.views import AttachmentDownloadView
from user_management.views import LoginView
from project.models import Project
from kanbancol.models import KanbanColumn
from issue.models import Issue, Attachment
from django.contrib.auth import get_user_model
from django.core.files import File

from common.settings import TEST_FILE_PATH, MEDIA_ROOT

proj_short = 'PRJ'


class AttachmentTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        # NOTE: if you modify those elements they need to be created in setUp, instead of here
        cls.user = get_user_model().objects.create_user('a', 'b', 'c')
        cls.user2 = get_user_model().objects.create_user('d', 'e', 'f')

    def setUp(self):
        # NOTE: these element gets modified by some of those tests, so they should NOT be created in setUpTestData()
        self.client.force_login(self.user)
        self.project = Project(creator=self.user, name_short=proj_short)
        self.project.save()
        self.project.manager.add(self.user)
        self.project.developer.add(self.user)
        self.column = KanbanColumn(name='Column', position=4, project=self.project)
        self.column.save()
        self.issue = Issue(title="Test-Issue", project=self.project, kanbancol=self.column, type="Bug")
        self.issue.save()

    def test_view_and_template(self):
        # TODO TESTCASE invite_users
        #      use view_and_template()
        # TODO which views?
        #      - issue:download_attachment
        #      - issue:delete_attachment
        #      - ...
        pass

    def test_redirect_to_login_and_login_required(self):
        self.client.logout()
        # TODO TESTCASE invite_users
        #      redirect_to_login_and_login_required()
        # TODO which views?
        #      - issue:download_attachment
        pass

    def test_attachments_from_other_issues_of_same_project_invisible(self):
        # TODO TESTCASE
        pass

    def test_upload_attachment_with_get_request_disabled(self):
        # TODO TESTCASE
        pass

    def test_file_size_restriction(self):
        # verify that the allowed file size (attachment) is actually limited
        huge_file = TEST_FILE_PATH+'/16mb.txt'
        f = open(huge_file, "r")
        file_dict = {
            "file": f,
        }
        response = self.client.post(reverse('issue:detail', kwargs={'project': self.project.name_short,
                                            'sqn_i': self.issue.number}), file_dict)
        f.close()
        # TODO TESTCASE execute in try-except block and delete the file in except
        self.assertContains(response, "The uploaded file exceeds the allowed file size of: ")

    def test_create_and_download_attachment(self):
        # create file for uploading
        filecontent = 'Hello World'
        temp = tempfile.NamedTemporaryFile(delete=False)
        temp.write(filecontent.encode())
        temp.close()

        f = File(open(temp.name, 'r'))
        attachment = Attachment(file=f, creator=self.user, issue=self.issue)
        attachment.save()
        f.close()
        # delete the uploaded file locally
        os.unlink(temp.name)

        issue = Issue.objects.get(pk=self.issue.pk)
        self.assertEqual(self.issue.attachments.count(), 1)
        attachment = self.issue.attachments.first()
        self.assertEqual(attachment.creator, self.user)
        self.assertEqual(attachment.seqnum, 1)
        self.assertEqual(attachment.issue.nextAttachmentId, 2)

        response = self.client.get(reverse('issue:download_attachment',
                                   kwargs={'project': proj_short, 'sqn_i': 1, 'sqn_a': attachment.seqnum}))
        self.assertEqual(response.status_code, 200)
        self.assertEqual("application/octet-stream", response.get('Content-Type'))
        self.assertEqual(response.resolver_match.func.__name__, AttachmentDownloadView.as_view().__name__)
        # delete the uploaded file from the server
        os.unlink(MEDIA_ROOT + '/' + attachment.file.name)

    def test_attachment_delete(self):
        # create sample attachment
        filecontent = 'Hello World'
        temp = tempfile.NamedTemporaryFile(delete=False)
        temp.write(filecontent.encode())
        temp.close()
        f = File(open(temp.name, 'r'))
        attachment = Attachment(file=f, creator=self.user, issue=self.issue)
        attachment.save()
        f.close()
        filePath = attachment.file.path
        self.assertTrue(os.path.isfile(filePath))

        # delete the attachment
        response = self.client.get(reverse('issue:delete_attachment',
                                           kwargs={'project': self.project.name_short,
                                                   'sqn_i': self.issue.number,
                                                   'sqn_a': attachment.seqnum}),
                                   follow=True)
        self.assertRedirects(response, reverse('issue:detail', kwargs={'project': self.project.name_short,
                                                                       'sqn_i': self.issue.number}))
        self.assertFalse(self.issue.attachments.all().exists())
        self.assertFalse(os.path.isfile(filePath))

        # delete temp file locally
        os.unlink(temp.name)

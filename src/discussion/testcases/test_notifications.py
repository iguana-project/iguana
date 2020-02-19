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

from project.models import Project
from issue.models import Issue, Comment, Attachment
from discussion.models import Notification
from django.contrib.auth import get_user_model
from django.core.files import File

from common.settings import MEDIA_ROOT

import os
import tempfile


class SignalTest(TestCase):
    short = 'proj'

    @classmethod
    def setUpTestData(cls):
        # NOTE: if you modify these elements they need to be created in setUp(), instead of here
        cls.user1 = get_user_model().objects.create_user('user1', 'mail', 'c')
        cls.user2 = get_user_model().objects.create_user('user2', 'othermail', 'c')
        cls.project = Project(creator=cls.user1, name_short=cls.short)
        cls.project.save()
        cls.project.developer.add(cls.user1)
        cls.project.developer.add(cls.user2)
        cls.project.manager.add(cls.user1)

    def test_create_issue(self):
        self.client.force_login(self.user1)

        res = self.client.get(reverse("discussion:list"))
        self.assertContains(res, "No unread messages.")

        # This should result in a notification
        issue = Issue(title="asdf", project=self.project)
        issue.save()

        res = self.client.get(reverse("discussion:list"))
        self.assertContains(res, "asdf")

        # This should remove the notification
        self.client.get(issue.get_absolute_url())

        res = self.client.get(reverse("discussion:list"))
        self.assertContains(res, "No unread messages.")

    def test_no_self_notification(self):
        self.client.force_login(self.user1)
        issue = Issue(title="asdf", project=self.project, creator=self.user1)
        issue.save()
        res = self.client.get(reverse("discussion:list"))
        self.assertContains(res, "No unread messages.")

    def test_comment(self):
        self.client.force_login(self.user1)
        issue = Issue(title="asdf", project=self.project, creator=self.user1)
        issue.save()

        Comment(creator=self.user2, issue=issue).save()
        res = self.client.get(reverse("discussion:list"))
        self.assertContains(res, "asdf")

        # Now user2 should also be a participant and receive notifications
        self.client.force_login(self.user2)
        self.client.get(issue.get_absolute_url())  # Clear notification from issue creation
        Comment(creator=self.user1, issue=issue).save()
        res = self.client.get(reverse("discussion:list"))
        self.assertContains(res, "asdf")
        self.client.force_login(self.user1)

    def test_notification_types_and_mention_feature(self):
        self.client.force_login(self.user1)
        issue = Issue(title="asdf", project=self.project, creator=self.user1)
        issue.save()

        # mention with bullshit input
        Comment(creator=self.user1, issue=issue, text='@everybody').save()
        self.assertEqual(self.user2.notifications.get(issue=issue).type.filter(type='Mention').count(), 0)
        self.assertEqual(self.user1.notifications.filter(issue=issue).count(), 0)
        Comment(creator=self.user1, issue=issue, text='@thisisnousername').save()
        self.assertEqual(self.user2.notifications.get(issue=issue).type.filter(type='Mention').count(), 0)
        self.assertEqual(self.user1.notifications.filter(issue=issue).count(), 0)

        # NewIssue-Type in notification
        self.assertEqual(self.user2.notifications.first().type.first().type, 'NewIssue')

        Comment(creator=self.user1, issue=issue, text='mention @user2').save()
        # NewIssue-Type plus Mention-Type in notification
        self.assertEqual(self.user2.notifications.first().type.first().type, 'NewIssue')
        self.assertEqual(self.user2.notifications.first().type.last().type, 'Mention')

        # user1 is following the issue because he created it
        comm = Comment(creator=self.user2, issue=issue, text='lets make a comment')
        comm.save()
        self.assertEqual(self.user1.notifications.first().type.first().type, 'NewComment')
        self.assertEqual(self.user1.notifications.first().type.first().comment, comm)

        comm.text = 'edited comment'
        comm.save()
        # NewComment-Type got replaced by EditComment-Type
        self.assertEqual(self.user1.notifications.first().type.first().type, 'EditComment')
        self.assertEqual(self.user1.notifications.first().type.first().comment, comm)
        self.assertEqual(self.user1.notifications.first().type.count(), 1)

        comm.text = 'mention @user1"'
        comm.save()
        # NewComment-Type got replaced by Mention-Type
        self.assertEqual(self.user1.notifications.first().type.first().type, 'Mention')
        self.assertEqual(self.user1.notifications.first().type.first().comment, comm)
        self.assertEqual(self.user1.notifications.first().type.count(), 1)

        comm.text = 'mentionedited @user1"'
        comm.save()
        # still Mention-Type
        self.assertEqual(self.user1.notifications.first().type.first().type, 'Mention')
        self.assertEqual(self.user1.notifications.first().type.first().comment, comm)
        self.assertEqual(self.user1.notifications.first().type.count(), 1)

        # third user for project
        user3 = get_user_model().objects.create_user('user3', 'mail@fail.com', 'c')
        self.project.developer.add(user3)

        issue2 = Issue(title="a new issue", project=self.project, creator=self.user1)
        issue2.save()
        self.assertEqual(user3.notifications.get(issue=issue2).type.filter(type="NewIssue").exists(), True)
        self.assertEqual(self.user2.notifications.get(issue=issue2).type.filter(type="NewIssue").exists(), True)

        comm2 = Comment(creator=self.user1, issue=issue2, text='@user2')
        comm2.save()
        comm2.text = 'lets make a comment with a all mention @all'
        comm2.save()

        # user1 created comment, mention for user2 and user3
        self.assertEqual(user3.notifications.get(issue=issue2).type.filter(comment=comm2, type="Mention").exists(),
                         True)
        self.assertEqual(self.user2.notifications.get(issue=issue2).type.filter(comment=comm2, type="Mention").exists(),
                         True)
        self.assertEqual(self.user1.notifications.filter(issue=issue2).count(), 0)

        comm3 = Comment(creator=self.user2, issue=issue2, text='lets make a comment from user2 with a all mention @all')
        comm3.save()

        # user2 created comment, mention for user1 and user3
        self.assertEqual(user3.notifications.get(issue=issue2).type.filter(type="Mention").count(), 2)
        self.assertEqual(self.user1.notifications.get(issue=issue2).type.filter(comment=comm3, type="Mention").exists(),
                         True)
        self.assertEqual(self.user2.notifications.get(issue=issue2).type.filter(comment=comm3, type="Mention").count(),
                         0)

        issue3 = Issue(title="test multiple comment notifications", project=self.project, creator=self.user1)
        issue3.save()
        # instant mention
        self.user2.notifications.get(issue=issue3).delete()
        mention = Comment(creator=self.user1, issue=issue3, text='@user2')
        mention.save()
        self.assertEqual(self.user2.notifications.get(issue=issue3).type.filter(type="Mention",
                                                                                comment=mention
                                                                                ).count(), 1)

        comm4 = Comment(creator=self.user2, issue=issue3, text='lets make a comment from user2')
        comm4.save()
        self.assertEqual(self.user1.notifications.get(issue=issue3).type.filter(type="NewComment").count(), 1)
        comm5 = Comment(creator=self.user2, issue=issue3, text='lets make another comment from user2')
        comm5.save()
        self.assertEqual(self.user1.notifications.get(issue=issue3).type.filter(type="NewComment").count(), 2)
        comm4.text = 'now a mention @user1'
        comm4.save()
        self.assertEqual(self.user1.notifications.get(issue=issue3).type.filter(type="NewComment").count(), 1)
        self.assertEqual(self.user1.notifications.get(issue=issue3).type.filter(type="Mention").count(), 1)
        comm5.text = 'now a mention @user1'
        comm5.save()
        self.assertEqual(self.user1.notifications.get(issue=issue3).type.filter(type="NewComment").count(), 0)
        self.assertEqual(self.user1.notifications.get(issue=issue3).type.filter(type="Mention").count(), 2)

        # test create comment trumped by edit comment trumped by mention
        comm6 = Comment(creator=self.user2, issue=issue2, text='lets make a comment from user2')
        comm6.save()
        self.assertEqual(self.user1.notifications.get(issue=issue2).type.filter(comment=comm6,
                                                                                type="NewComment"
                                                                                ).count(), 1)
        comm6.text = 'edited comment'
        comm6.save()
        self.assertEqual(self.user1.notifications.get(issue=issue2).type.filter(comment=comm6,
                                                                                type="NewComment"
                                                                                ).count(), 0)
        self.assertEqual(self.user1.notifications.get(issue=issue2).type.filter(comment=comm6,
                                                                                type="EditComment"
                                                                                ).count(), 1)
        # still one edit notification
        comm6.text = 'annother edit'
        comm6.save()
        self.assertEqual(self.user1.notifications.get(issue=issue2).type.filter(comment=comm6,
                                                                                type="EditComment"
                                                                                ).count(), 1)

        comm6.text = 'now a mention @user1'
        comm6.save()
        self.assertEqual(self.user1.notifications.get(issue=issue2).type.filter(comment=comm6,
                                                                                type="EditComment"
                                                                                ).count(), 0)
        self.assertEqual(self.user1.notifications.get(issue=issue2).type.filter(comment=comm6,
                                                                                type="Mention"
                                                                                ).count(), 1)
        number = comm6.seqnum

        # delete all notitypes for user1 on issue2 except the comm6 mention
        for notitype in self.user1.notifications.get(issue=issue2).type.all():
            if notitype.comment.seqnum == number:
                continue
            else:
                notitype.delete()

        # delete mention comme notification object gets deletedd
        comm6.delete()
        self.assertEqual(self.user1.notifications.filter(issue=issue2).count(), 0)

        # test attachment
        filecontent = 'Hello World'
        temp = tempfile.NamedTemporaryFile(delete=False)
        temp.write(filecontent.encode())
        temp.close()

        f = File(open(temp.name, 'r'))
        attachment = Attachment(file=f, creator=self.user2, issue=issue2)
        attachment.save()
        f.close()

        self.assertEqual(self.user1.notifications.get(issue=issue2).type.filter(type="NewAttachment").count(), 1)
        # delete the uploaded file from the server
        os.unlink(MEDIA_ROOT + '/' + attachment.file.name)
        # delete the uploaded file locally
        os.unlink(temp.name)

    def test_mute(self):
        self.client.force_login(self.user1)
        issue = Issue(title="asdf", project=self.project, creator=self.user1)
        issue.save()

        self.client.post(reverse("discussion:mute", kwargs={"project": self.short, "sqn_i": issue.number}))

        Comment(creator=self.user2, issue=issue).save()
        res = self.client.get(reverse("discussion:list"))
        self.assertContains(res, "No unread messages.")
        # test next post parameter
        response = self.client.post(reverse("discussion:follow", kwargs={"project": self.short, "sqn_i": issue.number}),
                                    {'next': '/timelog'},
                                    follow=True)
        self.assertRedirects(response, reverse('timelog:loginfo'))
        response = self.client.post(reverse("discussion:mute", kwargs={"project": self.short, "sqn_i": issue.number}),
                                    {'next': '/timelog'},
                                    follow=True)
        self.assertRedirects(response, reverse('timelog:loginfo'))

    def test_follow(self):
        issue = Issue(title="asdf", project=self.project, creator=self.user1)
        issue.save()

        self.client.force_login(self.user2)
        self.client.post(reverse("discussion:follow", kwargs={"project": self.short, "sqn_i": issue.number}))

        Comment(creator=self.user1, issue=issue).save()
        res = self.client.get(reverse("discussion:list"))
        self.assertContains(res, "asdf")

    def test_seen_all(self):
        self.client.force_login(self.user1)
        issue1 = Issue(title="iss1", project=self.project, creator=self.user2)
        issue1.save()
        issue2 = Issue(title="iss2", project=self.project, creator=self.user2)
        issue2.save()

        res = self.client.get(reverse("discussion:list"))
        self.assertContains(res, "iss1")
        self.assertContains(res, "iss2")

        self.client.post(reverse("discussion:seen", kwargs={'project': self.short}), {'issue': '-1'})
        res = self.client.get(reverse("discussion:list"))
        self.assertContains(res, "No unread messages.")

    def test_seen(self):
        self.client.force_login(self.user1)
        issue = Issue(title="iss1", project=self.project, creator=self.user2)
        issue.save()

        res = self.client.get(reverse("discussion:list"))
        self.assertContains(res, "iss1")

        self.client.post(reverse("discussion:seen", kwargs={'project': self.short}), {'issue': issue.number})
        res = self.client.get(reverse("discussion:list"))
        self.assertContains(res, "No unread messages.")

    def test_impact_of_notification_adjustment(self):
        # TODO TESTCASE test this after the adjustment of notification types via profile-page for discussion
        pass

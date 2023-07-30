"""
Iguana (c) by Marc Ammon, Moritz Fickenscher, Lukas Fridolin, Michael Gunselmann, Katrin Raab, Christian Strate

Iguana is licensed under BSD-2-Clause License.

Redistribution and use in source and binary forms, with or without modification,
are permitted provided that the following conditions are met:

   1. Redistributions of source code must retain the above copyright notice,
      this list of conditions and the following disclaimer.
   2. Redistributions in binary form must reproduce the above copyright notice,
      this list of conditions and the following disclaimer
      in the documentation and/or other materials provided with the distribution.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES,
INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS
BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
(INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS;
OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE,
EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
"""
from django.db.models.signals import post_save, pre_save, pre_delete, m2m_changed
from django.dispatch import receiver

from issue.models import Issue, Comment, Attachment
from discussion.models import Notification, Notitype
from common.tasks import send_discussion_mail
import re


def scan_mentions(sender, instance, **kwargs):
    members = instance.issue.project.get_members()
    mentions = re.findall(r"@\w+", instance.text)
    for mention in list(set(mentions)):
        username = mention[1:]
        if members.filter(username=username).exists():
            noti = members.get(username=username).notifications.filter(issue=instance.issue).first()
            if not noti:
                noti = Notification(user=members.get(username=username), issue=instance.issue)
                noti.save()
            noti_type = Notitype(type='Mention', comment=instance)
            noti_type.save()
            prev_noti_type = noti.type.filter(comment=instance)
            if prev_noti_type:
                for prevs in prev_noti_type:
                    noti.type.remove(prevs)
            noti.type.add(noti_type)
        elif username == 'all':
            for user in members.exclude(username=instance.creator.username):
                noti = user.notifications.filter(issue=instance.issue).first()
                if not noti:
                    noti = Notification(user=user, issue=instance.issue)
                    noti.save()
                noti_type = Notitype(type='Mention', comment=instance)
                noti_type.save()
                prev_noti_type = noti.type.filter(comment=instance)
                if prev_noti_type:
                    for prevs in prev_noti_type:
                        noti.type.remove(prevs)
                noti.type.add(noti_type)


post_save.connect(scan_mentions, sender=Comment, dispatch_uid="scan_mentions_post_save")


@receiver(post_save, sender=Issue)
def new_issue(sender, instance, created, *args, **kwargs):
    if created:
        if instance.creator:
            instance.participant.add(instance.creator)
        for user in instance.project.get_members():
            if not user == instance.creator:
                noti = Notification(user=user, issue=instance)
                noti.save()
                noti_type = Notitype(type='NewIssue')
                noti_type.save()
                noti.type.add(noti_type)


@receiver(post_save, sender=Comment)
@receiver(post_save, sender=Attachment)
def new_discussion_entry(sender, instance, created, *args, **kwargs):
    for user in instance.issue.participant.all():
        if not user == instance.creator:
            noti = Notification.objects.filter(user=user, issue=instance.issue).first()
            if not noti:
                noti = Notification(user=user, issue=instance.issue)
                noti.save()
            if sender == Comment and created:
                prev_noti_type = noti.type.filter(comment=instance, type='Mention')
                if prev_noti_type:
                    continue
                noti_type = Notitype(type='NewComment', comment=instance)
                noti_type.save()
                noti.type.add(noti_type)
            elif sender == Comment:
                noti_type = Notitype(type='EditComment', comment=instance)
                noti_type.save()
                prev_noti_type = noti.type.filter(comment=instance, type='NewComment')
                if prev_noti_type:
                    for prevs in prev_noti_type:
                        noti.type.remove(prevs)
                prev_noti_type = noti.type.filter(comment=instance, type='EditComment')
                if prev_noti_type:
                    for prevs in prev_noti_type:
                        noti.type.remove(prevs)
                prev_noti_type = noti.type.filter(comment=instance, type='Mention')
                if prev_noti_type:
                    continue
                noti.type.add(noti_type)
            else:
                noti_type = Notitype(type='NewAttachment')
                noti_type.save()
                noti.type.add(noti_type)
    instance.issue.participant.add(instance.creator)


@receiver(pre_delete, sender=Comment)
def comment_delete(sender, instance,  *args, **kwargs):
    notis = Notification.objects.filter(issue=instance.issue)
    for noti in notis:
        prev_noti_type = noti.type.filter(comment=instance)
        for prev in prev_noti_type:
            prev.delete()
        if not noti.type.all():
            noti.delete()


@receiver(m2m_changed, sender=Notification.type.through)
def save_notification(sender, instance, *args, **kwargs):
    # update latest_modification for the notification instance
    instance.save()
    if kwargs['action'] == 'post_add':
        send_discussion_mail.delay(instance.pk)

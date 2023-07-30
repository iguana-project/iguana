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
from django.db import models
from django.utils import timezone
from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.db import IntegrityError, transaction
from django.core.cache import cache

import datetime
from .validators import *
from issue.models import *

from lib.custom_model import CustomModel

from django.utils.translation import ugettext_lazy as _


class Timelog(CustomModel):
    number = models.IntegerField(_("Timelog number"), editable=False, default=-1)
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             on_delete=models.CASCADE,
                             verbose_name=_("logger"),
                             related_name="logged_on"
                             )

    issue = models.ForeignKey(Issue,
                              on_delete=models.CASCADE,
                              verbose_name=_("issue"),
                              related_name="logs"
                              )

    created_at = models.DateTimeField(_("Start Date"), default=timezone.now, validators=[date_is_present_or_past])
    updated_at = models.DateTimeField(_("Last updated:"), auto_now=True)
    time = models.DurationField(_("Time"),  validators=[logged_time_is_positive])

    class Meta:
        ordering = ['created_at']
        verbose_name = _("timelog")
        verbose_name_plural = _("timelogs")

    # time logging for a user is allowed by the user itself and by project-managers
    # modification of time logs is not possible when not part of the project anymore
    def edit_allowed(self, user):
        if self.issue.project.is_manager(user) or (user == self.user and self.issue.user_has_read_permissions(user)):
            return 1
        return 0

    def __str__(self):
        return "logged time: {} for issue: {}".format(self.time, self.issue)

    # TODO
    # def search_allowed_for_user(self, user):

    def user_has_write_permissions(self, user):
        return self.edit_allowed(user)

    def user_has_read_permissions(self, user):
        return self.issue.project.user_has_read_permissions(user)

    # TODO
    # def activity_stream_long_name(self):


@transaction.atomic
@receiver(pre_save, sender=Timelog)
def my_callback(sender, instance, *args, **kwargs):
    # TODO replaces the microseconds of the DateTimeField before saving the value, but y?
    now = timezone.now()
    if instance.created_at + instance.time > now:
        instance.created_at -= instance.time
    instance.created_at = instance.created_at.replace(microsecond=100000)
    old = Timelog.objects.filter(id=instance.id)
    if old.exists():
        instance.issue.logged_total -= old.first().time
    instance.issue.logged_total += instance.time
    instance.issue.save()
    return


@receiver(pre_save, sender=Timelog)
def set_timelog_number(sender, instance, *args, **kwargs):
    if instance.number == -1:
        instance.number = get_number_for_timelog(instance.issue)

        # because we have two issue.save() calls after timelog creation
        instance.issue.project.increase_activity(timezone.now(), decrease=True)
    cache.delete('action_data_'+instance.user.username+'_'+instance.issue.project.name_short)
    cache.delete('action_data_'+instance.user.username)
    return


class Punch(CustomModel):
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             on_delete=models.CASCADE,
                             verbose_name=_("logger"),
                             related_name="punched_on"
                             )

    issue = models.ForeignKey(Issue,
                              on_delete=models.CASCADE,
                              verbose_name=_("issue"),
                              related_name="punched"
                              )
    created_at = models.DateTimeField(_("Punch Start"), default=timezone.now, validators=[date_is_present_or_past])

    class Meta:
        verbose_name = _("Punch")
        verbose_name_plural = _("Punches")

    def user_has_write_permissions(self, user):
        return self.edit_allowed(user)

    def user_has_read_permissions(self, user):
        return self.issue.project.user_has_read_permissions(user)

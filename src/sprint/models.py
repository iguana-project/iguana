"""
Iguana (c) by Marc Ammon, Moritz Fickenscher, Lukas Fridolin,
Michael Gunselmann, Katrin Raab, Christian Strate

Iguana is licensed under a
Creative Commons Attribution-ShareAlike 4.0 International License.

You should have received a copy of the license along with this
work. If not, see <http://creativecommons.org/licenses/by-sa/4.0/>.
"""
from django.db import models
from django.db.models.signals import pre_save
from django.db import transaction
from django.dispatch import receiver
from django.urls import reverse

import datetime

from common.validators import date_is_present_or_future
from project.models import Project

from django.utils.translation import ugettext_lazy as _
from lib.custom_model import CustomModel


@transaction.atomic
def get_number_for_sprint(project):
    retval = project.nextSprintId
    project.nextSprintId += 1
    project.save()
    return retval


# no CustomModel required since object is used within models.py only
class SprintQuerySet(models.QuerySet):
    def get_current_sprints(self):
        return self.filter(startdate__isnull=False, enddate__isnull=True)

    def get_new_sprints(self):
        return self.filter(startdate__isnull=True, enddate__isnull=True)

    def get_old_sprints(self):
        return self.filter(startdate__isnull=False, enddate__isnull=False)

    def unstopped(self):
        return self.filter(enddate__isnull=True)


class Sprint(CustomModel):
    seqnum = models.IntegerField(_("Sprint number"), editable=False, default=-1)
    project = models.ForeignKey(Project, models.CASCADE, verbose_name=_("project"), related_name="sprint")
    startdate = models.DateField(_("Start_Date"),
                                 validators=[
                                    date_is_present_or_future
                                 ],
                                 default=None,
                                 blank=True,
                                 null=True
                                 )
    enddate = models.DateField(_("End_Date"),
                               validators=[
                                   date_is_present_or_future
                               ],
                               default=None,
                               blank=True,
                               null=True
                               )
    plandate = models.DateField(_("Planned Enddate"),
                                validators=[date_is_present_or_future],
                                default=None,
                                blank=True,
                                null=True,
                                )
    objects = SprintQuerySet.as_manager()

    class Meta:
        base_manager_name = 'objects'
        verbose_name = _("sprint")
        verbose_name_plural = _("sprints")

    def get_absolute_url(self):
        return reverse('backlog:backlog', kwargs={'project': self.project.name_short, 'sqn_s': self.seqnum})

    def is_active(self):
        return (self.startdate is not None) and (self.enddate is None)

    def issues_left(self):
        return self.issue.exclude(kanbancol__type='Done')

    def set_active(self):
        self.startdate = datetime.datetime.now()
        self.save()
        return

    def is_inactive(self):
        return (self.startdate is not None) and (self.enddate is not None)

    def set_inactive(self):
        issues_left = False
        issues = self.issue.all()
        issues_left = list(self.issue.exclude(kanbancol__type='Done'))
        for issue in issues:
            issue.was_in_sprint = True

            # if issue is not done put it back to backlog
            if issue.kanbancol.type != 'Done':
                issue.sprint = None
            # if issue is done archive it. flag is for message
            if issue.kanbancol.type == 'Done':
                issue.archived = True
            issue.save()
        if not self.startdate:
            self.startdate = datetime.datetime.now()
        self.enddate = datetime.datetime.now()
        self.save()
        if self.project.currentsprint == self:
            self.project.currentsprint = None
            self.project.save()
        return issues_left

    def __str__(self):
        return 'Sprint ' + str(self.seqnum) + ' of project ' + str(self.project)

    def user_has_write_permissions(self, user):
        return self.project.user_has_write_permissions(self, user)

    def user_has_read_permissions(self, user):
        return self.project.user_has_read_permissions(user)

    def activity_stream_short_name(self):
        return 'Sprint ' + str(self.seqnum)

    def activity_stream_long_name(self):
        return self.__str__()


@receiver(pre_save, sender=Sprint)
def set_attachment_number(sender, instance, *args, **kwargs):
    if instance.seqnum == -1:
        instance.seqnum = get_number_for_sprint(instance.project)
        # TODO BUG is there an instance.save() missing? if not please comment here y not
    return

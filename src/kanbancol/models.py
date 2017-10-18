"""
Iguana (c) by Marc Ammon, Moritz Fickenscher, Lukas Fridolin,
Michael Gunselmann, Katrin Raab, Christian Strate

Iguana is licensed under a
Creative Commons Attribution-ShareAlike 4.0 International License.

You should have received a copy of the license along with this
work. If not, see <http://creativecommons.org/licenses/by-sa/4.0/>.
"""
from django.db import models, transaction
from django.core import validators
from django.urls import reverse

from project.models import Project
from lib.custom_model import CustomModel

from django.utils.translation import ugettext_lazy as _


class KanbanColumn(CustomModel):
    name = models.CharField(_("name"), max_length=100)
    project = models.ForeignKey(Project, models.CASCADE, verbose_name=_('project'), related_name="kanbancol")
    position = models.IntegerField(_("position"))

    COLUMN_TYPES = (
        ('ToDo', _("Todo")),
        ('InProgress', _("In Progress")),
        ('Done', _("Done")),
    )
    type = models.CharField(
        _("Type"),
        max_length=10,
        choices=COLUMN_TYPES,
        default='ToDo',
    )

    class Meta:
        ordering = ['position']
        verbose_name = _("kanbancolumn")
        verbose_name_plural = _("kanbancolumns")

    @transaction.atomic
    def switch(self, pos):
        try:
            other = KanbanColumn.objects.get(project=self.project, position=pos)
        except KanbanColumn.DoesNotExist:
            return
        other.position = self.position
        other.save()
        self.position = pos
        self.save()

    def save(self, *args, **kwargs):
        if self.position is None:
            n = KanbanColumn.objects.filter(project=self.project).count()
            self.position = n
        super(KanbanColumn, self).save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        super(KanbanColumn, self).delete(*args, **kwargs)
        qs = KanbanColumn.objects.filter(project=self.project).order_by('position')
        for i, kc in enumerate(qs):
            kc.position = i
            kc.save()

    def __str__(self):
        return self.name

    def search_allowed_for_user(self, user):
        # TODO TESTCASE
        pass

    def user_has_write_permissions(self, user):
        return self.project.user_has_write_permissions(user)

    def user_has_read_permissions(self, user):
        return self.project.user_has_read_permissions(user)

    def activity_stream_long_name(self):
        # TODO TESTCASE
        pass

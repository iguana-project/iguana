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
from django.db import models, transaction
from django.core import validators
from django.urls import reverse

from project.models import Project
from lib.custom_model import CustomModel

from django.utils.translation import ugettext_lazy as _
from search.fieldcheckings import SearchableMixin


class KanbanColumn(SearchableMixin, CustomModel):
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
    searchable_fields = ['name', 'type']

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

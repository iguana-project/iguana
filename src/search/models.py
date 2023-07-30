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
from django.db.models.signals import post_save
from django.dispatch import receiver

from common.settings import AUTH_USER_MODEL
from lib.custom_model import CustomModel

from django.utils.translation import ugettext_lazy as _


class Search(CustomModel):
    description = models.CharField(_("Description"), max_length=100)
    searchexpression = models.CharField(_("Expression"), max_length=200)
    creator = models.ForeignKey(AUTH_USER_MODEL,
                                models.CASCADE,
                                verbose_name=_("creator"),
                                related_name="searches")
    shared_with = models.ManyToManyField('project.Project',
                                         verbose_name=_("shared with"),
                                         related_name="searches",
                                         blank=True)
    persistent = models.BooleanField(_("Persistent"), default=False)

    class Meta:
        ordering = ['-pk']
        verbose_name = _("search")
        verbose_name_plural = _("searches")

    def user_has_read_permissions(self, user):
        if self.creator == user:
            return 1
        for project in self.shared_with.all():
            if project.user_has_read_permissions(user):
                return 1
        return 0

    def user_has_write_permissions(self, user):
        if self.creator == user:
            return 1
        for project in self.shared_with.all():
            if project.user_has_write_permissions(user):
                return 1
        return 0

    def __str__(self):
        return "{}".format(self.searchexpression)


@receiver(post_save, sender=Search)
def delete_nonpersistents(sender, instance, *args, **kwargs):
    # keep only 10 non-persistent issues
    qresult = Search.objects.filter(persistent=False).order_by('-pk')[10:]
    for toDelete in qresult:
        toDelete.delete()

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
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _

from common import settings
from lib.custom_model import CustomModel


# no need to inherit from CustomModel since it doesn't contain personal information
class Notitype(models.Model):
    NOTI_TYPES = (
        ('Mention', _("Mention")),
        ('NewComment', _("New comment")),
        ('NewAttachment', _("New attachment")),
        ('EditComment', _("Comment edited")),
        ('NewIssue', _("New issue")),
    )

    comment = models.ForeignKey('issue.Comment', models.SET_NULL, verbose_name=_('issue'), blank=True, null=True)

    type = models.CharField(
        _("Type"),
        max_length=15,
        choices=NOTI_TYPES,
        default='NewComment',
    )

    def __str__(self):
        return self.type


class Notification(CustomModel):
    issue = models.ForeignKey('issue.Issue', models.CASCADE, verbose_name=_('issue'), editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        models.CASCADE,
        verbose_name=_("user"),
        related_name="notifications",
        blank=False,
        editable=False,
        )

    # updates the value every time the object is saved
    # due to the m2m_changed signal this is saved also in case of an added type etc.
    latest_modification = models.DateTimeField(auto_now=True)

    type = models.ManyToManyField(Notitype,
                                  verbose_name=_("notitype"),
                                  related_name="notifications",
                                  )

    def __str__(self):
        return "{}: {})".format(self.issue, [str(typ) for typ in self.type.all()])

    class Meta:
        unique_together = ('issue', 'user')
        # latest updates shall be placed on top
        ordering = ['-latest_modification']

    def user_has_write_permissions(self, user):
        return self.user == user and self.issue.user_has_read_permissions(user)

    def user_has_read_permissions(self, user):
        return self.user == user and self.issue.user_has_read_permissions(user)

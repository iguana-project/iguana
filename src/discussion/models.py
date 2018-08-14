"""
Iguana (c) by Marc Ammon, Moritz Fickenscher, Lukas Fridolin,
Michael Gunselmann, Katrin Raab, Christian Strate

Iguana is licensed under a
Creative Commons Attribution-ShareAlike 4.0 International License.

You should have received a copy of the license along with this
work. If not, see <http://creativecommons.org/licenses/by-sa/4.0/>.
"""
from django.db import models
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _

from common import settings


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


class Notification(models.Model):
    issue = models.ForeignKey('issue.Issue', models.CASCADE, verbose_name=_('issue'), editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        models.CASCADE,
        verbose_name=_("user"),
        related_name="notifications",
        blank=False,
        editable=False,
        )

    # updates the value everytime the object is saved
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

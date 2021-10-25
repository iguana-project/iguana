"""
Iguana (c) by Marc Ammon, Moritz Fickenscher, Lukas Fridolin,
Michael Gunselmann, Katrin Raab, Christian Strate

Iguana is licensed under a
Creative Commons Attribution-ShareAlike 4.0 International License.

You should have received a copy of the license along with this
work. If not, see <http://creativecommons.org/licenses/by-sa/4.0/>.
"""
from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.conf import settings


from lib.custom_model import CustomModel


# filter for the "Your issues" page
class Filter(CustomModel):
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             models.CASCADE,
                             verbose_name=_("user"),
                             related_name="filters",
                             blank=False,
                             editable=False,
                             )
    typ = models.CharField(_("Typ"), max_length=99)
    queryset = models.CharField(_("Filter"), max_length=999)
    name = models.CharField(_("Name"), max_length=99)

    def user_has_write_permissions(self, user):
        return self.user == user

    def user_has_read_permissions(self, user):
        return self.user == user

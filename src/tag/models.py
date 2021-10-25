"""
Iguana (c) by Marc Ammon, Moritz Fickenscher, Lukas Fridolin,
Michael Gunselmann, Katrin Raab, Christian Strate

Iguana is licensed under a
Creative Commons Attribution-ShareAlike 4.0 International License.

You should have received a copy of the license along with this
work. If not, see <http://creativecommons.org/licenses/by-sa/4.0/>.
"""
import random

from django.db import models
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _

from lib.custom_model import CustomModel
from project.models import Project
from search.fieldcheckings import SearchableMixin


class Tag(SearchableMixin, CustomModel):
    tag_text = models.CharField(_('text'), max_length=32)

    # NOTE since there is no allow-null field, you have to provide a default value during makemigrations
    # NOTE therefore you can provide - (0) - without any quotings.
    project = models.ForeignKey(Project, models.CASCADE, verbose_name=_('project'), related_name='tags')

    # Material colors
    COLORS = (
        ("e91e63", _("pink")),
        ("f44336", _("red")),
        ("9c27b0", _("purple")),
        ("673ab7", _("deep purple")),
        ("3f51b5", _("indigo")),
        ("2196f3", _("blue")),
        ("03a9f4", _("light blue")),
        ("00bcd4", _("cyan")),
        ("009688", _("teal")),
        ("4caf50", _("green")),
        ("8bc34a", _("light green")),
        ("cddc39", _("lime")),
        ("ffeb3b", _("yellow")),
        ("ffc107", _("amber")),
        ("ff9800", _("orange")),
        ("ff5722", _("deep orange")),
        ("795548", _("brown")),
        ("9e9e9e", _("grey")),
        ("607d8b", _("blue grey")),
    )

    # Colors that need a black font
    BRIGHT_COLORS = ["8bc34a", "cddc39", "ffeb3b", "ffc107", "ff9800", "9e9e9e"]

    # stores the color-hex value as string
    color = models.CharField(_('color'), choices=COLORS, max_length=32, blank=True)
    font_color = models.CharField(_('font color'), max_length=32, default="fff", editable=False)

    class Meta:
        ordering = ('tag_text',)
        unique_together = ('project', 'tag_text')
        verbose_name = _("tag")
        verbose_name_plural = _("tags")

    def __str__(self):
        return "{}".format(self.tag_text)

    def set_random_color(self):
        pool = set([a for a, b in self.COLORS])
        used = set([t.color for t in Tag.objects.filter(project=self.project)])
        used.remove('')  # I'm not sure where this rogue element comes from
        if len(used) < len(pool):
            pool -= used
        self.color = random.choice(list(pool))
        self.save()

    def get_absolute_url(self):
        return reverse('tag:tag', kwargs={'project': self.project.name_short})

    # SearchableMixin functions
    def search_allowed_for_user(self, user):
        return self.project.developer_allowed(user)

    def get_relative_project(self):
        return self.project.name

    def user_has_write_permissions(self, user):
        return self.project.user_has_write_permissions(user)

    def user_has_read_permissions(self, user):
        return self.project.user_has_read_permissions(user)

    searchable_fields = ['tag_text']

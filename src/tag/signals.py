"""
Iguana (c) by Marc Ammon, Moritz Fickenscher, Lukas Fridolin,
Michael Gunselmann, Katrin Raab, Christian Strate

Iguana is licensed under a
Creative Commons Attribution-ShareAlike 4.0 International License.

You should have received a copy of the license along with this
work. If not, see <http://creativecommons.org/licenses/by-sa/4.0/>.
"""
from django.db.models.signals import post_save
from django.dispatch import receiver

from tag.models import Tag


@receiver(post_save, weak=False, dispatch_uid='tag_create', sender=Tag)
def create_project_default_columns(sender, instance, created, **kwargs):
    if created:
        if not instance.color:
            instance.set_random_color()
        if instance.color in Tag.BRIGHT_COLORS:
            instance.font_color = "000"
            instance.save()

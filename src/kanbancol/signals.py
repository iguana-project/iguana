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
from kanbancol.models import KanbanColumn
from project.models import Project


@receiver(post_save, weak=False, dispatch_uid='project_create', sender=Project)
def create_project_default_columns(sender, **kwargs):
    if kwargs['created']:
        KanbanColumn(name='Todo', type='ToDo', project=kwargs['instance']).save()
        KanbanColumn(name='In Progress', type='InProgress', project=kwargs['instance']).save()
        KanbanColumn(name='Done', type='Done', project=kwargs['instance']).save()

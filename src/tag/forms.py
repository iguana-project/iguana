"""
Iguana (c) by Marc Ammon, Moritz Fickenscher, Lukas Fridolin,
Michael Gunselmann, Katrin Raab, Christian Strate

Iguana is licensed under a
Creative Commons Attribution-ShareAlike 4.0 International License.

You should have received a copy of the license along with this
work. If not, see <http://creativecommons.org/licenses/by-sa/4.0/>.
"""
from django.forms import ModelForm, ValidationError
from dal import autocomplete

from project.models import Project
from tag.models import Tag

from django.utils.translation import ugettext_lazy as _


class TagForm(ModelForm):
    project = ""

    class Meta:
        model = Tag
        fields = ['tag_text', 'color']
        widget = {
            'color': autocomplete.ModelSelect2(),
        }

    def __init__(self, *args, **kwargs):
        self.project = kwargs.pop('project')
        super(TagForm, self).__init__(*args, **kwargs)

    def clean_tag_text(self):
        tags = Tag.objects.filter(project=self.project)
        tag_to_be_stored = self.cleaned_data['tag_text']
        for tag in tags:
            if tag.tag_text == tag_to_be_stored:
                raise ValidationError(_('There is already a Tag "{}" for this project'.format(tag_to_be_stored) +
                                        ' and you are only allowed to have it once per project.'))
        return tag_to_be_stored

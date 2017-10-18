"""
Iguana (c) by Marc Ammon, Moritz Fickenscher, Lukas Fridolin,
Michael Gunselmann, Katrin Raab, Christian Strate

Iguana is licensed under a
Creative Commons Attribution-ShareAlike 4.0 International License.

You should have received a copy of the license along with this
work. If not, see <http://creativecommons.org/licenses/by-sa/4.0/>.
"""
from django.forms import ModelForm
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _

from .models import KanbanColumn


class KanbanColumnForm(ModelForm):
    class Meta:
        model = KanbanColumn
        fields = ('name', 'type')

    def clean(self):
        super(ModelForm, self).clean()
        type = self.cleaned_data.get('type')
        obj = self.save(commit=False)
        if obj.type == 'Done' and type != 'Done' and obj.project.kanbancol.filter(type='Done').count() == 1:
            raise ValidationError(_("This is the last column with type Done in this project, edit rejected"))
        if obj.type == 'ToDo' and type != 'ToDo' and obj.project.kanbancol.filter(type='ToDo').count() == 1:
            raise ValidationError(_("This is the last column with type ToDo in this project, edit rejected"))
        name = self.cleaned_data.get('name')
        test = obj.project.kanbancol.filter(name=name)
        if test.exists() and test.first().position is not obj.position:
            raise ValidationError(_("There is already a column with this name"))
        return self.cleaned_data

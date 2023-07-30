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

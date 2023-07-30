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
from django.forms import ModelForm, ValidationError

from tag.models import Tag

from django.utils.translation import ugettext_lazy as _
from common.widgets import CustomAutoCompleteWidgetSingle


class TagForm(ModelForm):
    project = ""

    class Meta:
        model = Tag
        fields = ['tag_text', 'color']
        widget = {
            'color': CustomAutoCompleteWidgetSingle(),
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

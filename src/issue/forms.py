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
from django.forms import ModelForm, CharField
from django.urls import reverse_lazy
from django.forms.widgets import NumberInput

from .models import Issue, Comment, Attachment
from django.utils.translation import ugettext as _nl

from image_strip.image_strip import strip_if_file_is_an_img
from common.widgets import CustomPagedownWidget, LocalizedDatePickerInput,\
    CustomAutoCompleteWidgetMultiple


class LimitKanbanForm(ModelForm):
    def __init__(self, proj, issue, *args, **kwargs):
        super(LimitKanbanForm, self).__init__(*args, **kwargs)
        self.fields['assignee'].widget = CustomAutoCompleteWidgetMultiple(reverse_lazy('project:userac',
                                                                                       kwargs={"project": proj}
                                                                                       ),
                                                                          attrs={'data-html': 'true'}
                                                                          )
        self.fields['assignee'].widget.choices = self.fields['assignee'].choices
        if issue is not None:  # issue-edit
            self.fields['dependsOn'].widget = CustomAutoCompleteWidgetMultiple(reverse_lazy('project:issueac',
                                                                                            kwargs={"project": proj,
                                                                                                    "issue": issue
                                                                                                    }
                                                                                            ),
                                                                               attrs={'data-html': 'true'}
                                                                               )
        else:   # issue-create
            self.fields['dependsOn'].widget = CustomAutoCompleteWidgetMultiple(reverse_lazy('project:issueac',
                                                                                            kwargs={"project": proj}
                                                                                            ),
                                                                               attrs={'data-html': 'true'}
                                                                               )
        self.fields['dependsOn'].widget.choices = self.fields['dependsOn'].choices
        # NOTE: data-html true could become a problem, when users can input their own colors
        self.fields['tags'].widget = CustomAutoCompleteWidgetMultiple(reverse_lazy('project:tagac',
                                                                                   kwargs={"project": proj}
                                                                                   ),
                                                                      attrs={'data-html': 'true'}
                                                                      )
        self.fields['tags'].widget.choices = self.fields['tags'].choices
        self.fields['title'].widget.attrs['autofocus'] = 'autofocus'

    description = CharField(widget=CustomPagedownWidget(), required=False)

    class Meta:
        model = Issue
        fields = ['title', 'kanbancol', 'due_date', 'type', 'assignee',
                  'priority', 'description', 'storypoints', 'dependsOn', 'tags']
        widgets = {
            # Use localization and bootstrap 3
            'due_date': LocalizedDatePickerInput(attrs={'id': "due_date"}),
            'storypoints': NumberInput(attrs={'min': 0})
        }


class CommentForm(ModelForm):
    text = CharField(widget=CustomPagedownWidget(attrs={'rows': 3}))

    class Meta:
        model = Comment
        fields = ['text']


attachment_help_text = _nl("Please make sure that you don't violate any copyright by uploading files. "
                           "Also keep in mind that any previous metadata of images will be removed.")


class AttachmentForm(ModelForm):
    class Meta:
        model = Attachment
        fields = ['file']
        help_texts = {
            'file': ("<div class='alert alert-warning'><b>NOTE:</b> " + attachment_help_text + "</div>")
        }

    def clean_file(self):
        cleaned_file = self.cleaned_data['file']
        # if the file is an image the metadata is stripped
        return strip_if_file_is_an_img(cleaned_file)

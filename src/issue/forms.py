"""
Iguana (c) by Marc Ammon, Moritz Fickenscher, Lukas Fridolin,
Michael Gunselmann, Katrin Raab, Christian Strate

Iguana is licensed under a
Creative Commons Attribution-ShareAlike 4.0 International License.

You should have received a copy of the license along with this
work. If not, see <http://creativecommons.org/licenses/by-sa/4.0/>.
"""
from django.forms import ModelForm, CharField
from django.urls import reverse_lazy
from django.forms.widgets import NumberInput
from dal import autocomplete

from .models import Issue, Comment, Attachment
from django.utils.translation import ugettext as _nl

from image_strip.image_strip import strip_if_file_is_an_img
from common.widgets import CustomPagedownWidget, LocalizedDateTimePickerInput


class LimitKanbanForm(ModelForm):
    def __init__(self, proj, issue, *args, **kwargs):
        super(LimitKanbanForm, self).__init__(*args, **kwargs)
        self.fields['assignee'].widget = autocomplete.ModelSelect2Multiple(reverse_lazy('project:userac',
                                                                                        kwargs={"project": proj}
                                                                                        ),
                                                                           attrs={'data-html': 'true'}
                                                                           )
        self.fields['assignee'].widget.choices = self.fields['assignee'].choices
        if issue is not None:  # issue-edit
            self.fields['dependsOn'].widget = autocomplete.ModelSelect2Multiple(reverse_lazy('project:issueac',
                                                                                             kwargs={"project": proj,
                                                                                                     "issue": issue
                                                                                                     }
                                                                                             ),
                                                                                attrs={'data-html': 'true'}
                                                                                )
        else:   # issue-create
            self.fields['dependsOn'].widget = autocomplete.ModelSelect2Multiple(reverse_lazy('project:issueac',
                                                                                             kwargs={"project": proj}
                                                                                             ),
                                                                                attrs={'data-html': 'true'}
                                                                                )
        self.fields['dependsOn'].widget.choices = self.fields['dependsOn'].choices
        # NOTE: data-html true could become a problem, when users can input their own colors
        self.fields['tags'].widget = autocomplete.ModelSelect2Multiple(reverse_lazy('project:tagac',
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
            'due_date': LocalizedDateTimePickerInput(attrs={'id': "due_date"}),
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

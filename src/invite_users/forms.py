"""
Iguana (c) by Marc Ammon, Moritz Fickenscher, Lukas Fridolin,
Michael Gunselmann, Katrin Raab, Christian Strate

Iguana is licensed under a
Creative Commons Attribution-ShareAlike 4.0 International License.

You should have received a copy of the license along with this
work. If not, see <http://creativecommons.org/licenses/by-sa/4.0/>.
"""
from django.forms import Form, BaseFormSet, CharField, EmailField, Textarea, ValidationError, formset_factory
from django.conf import settings

from django.utils.translation import ugettext_lazy as _

email_field_label = _('email of person to be invited')


class EmailFormField(Form):
    email = EmailField(label=email_field_label)


class EmailFormSet(BaseFormSet):
    def clean(self):
        # verify that all entered emails are distinct
        if any(self.errors):
            return
        emails = []
        for form in self.forms:
            email = form.cleaned_data.get('email')
            # NOTE: this None exclusion is important! fill field, add more, add more, invite => failure
            if email in emails and email is not None:
                raise ValidationError(_("You entered the same email twice. Each member can be invited only once."),
                                      code='duplicated_email')
            emails.append(email)
        return emails

    def add_fields(self, form, index):
        form.fields["email"] = EmailField(label=email_field_label)


class InviteUserForm(Form):
    additional_message = CharField(label=_('optional additional message'), max_length=300, required=False,
                                   widget=Textarea(attrs={'rows': 8, 'cols': 80}))

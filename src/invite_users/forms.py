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

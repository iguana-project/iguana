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
from django.forms import PasswordInput, ValidationError
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model

from captcha.fields import CaptchaField

from django.utils.translation import ugettext_lazy as _


class RegistrationForm(UserCreationForm):
    def __init__(self, *args, **kwargs):
        super(UserCreationForm, self).__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.pop('autofocus', None)

    captcha = CaptchaField()

    class Meta:

        model = get_user_model()
        widgets = {
            'password': PasswordInput()
        }
        help_texts = {
            'username': _('Required. 150 characters or fewer. Letters, digits and ./+/-/_ only.'),
            # NOTE: it seems like there is no clean way to show the help_text for password-field, because it's part
            #       of the PasswordInput-widget, so the help text is hardcoded in the template
        }
        fields = ('email', 'username')

    # disallow '@' in username
    def clean_username(self):
        username = self.cleaned_data['username']
        if '@' in username:
            raise ValidationError(_("@ is not allowed in username. Username is required as 150 characters or " +
                                    "fewer. Letters, digits and ./+/-/_ only."), code="invalid")
        return username

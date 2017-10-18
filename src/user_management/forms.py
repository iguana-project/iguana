"""
Iguana (c) by Marc Ammon, Moritz Fickenscher, Lukas Fridolin,
Michael Gunselmann, Katrin Raab, Christian Strate

Iguana is licensed under a
Creative Commons Attribution-ShareAlike 4.0 International License.

You should have received a copy of the license along with this
work. If not, see <http://creativecommons.org/licenses/by-sa/4.0/>.
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

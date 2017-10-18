"""
Iguana (c) by Marc Ammon, Moritz Fickenscher, Lukas Fridolin,
Michael Gunselmann, Katrin Raab, Christian Strate

Iguana is licensed under a
Creative Commons Attribution-ShareAlike 4.0 International License.

You should have received a copy of the license along with this
work. If not, see <http://creativecommons.org/licenses/by-sa/4.0/>.
"""
import datetime

from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _


def date_is_present_or_future(value):
    if type(value) is datetime.date:
        if value < datetime.date.today():
            raise ValidationError(
                _("Enter a date starting from today")
            )
    elif type(value) is datetime.datetime:
        if value < datetime.datetime.today():
            raise ValidationError(
                _("Enter a date starting from today")
            )
    else:
        raise ValidationError(
            _("Enter a date starting from today")
        )

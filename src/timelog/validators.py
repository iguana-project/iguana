"""
Iguana (c) by Marc Ammon, Moritz Fickenscher, Lukas Fridolin,
Michael Gunselmann, Katrin Raab, Christian Strate

Iguana is licensed under a
Creative Commons Attribution-ShareAlike 4.0 International License.

You should have received a copy of the license along with this
work. If not, see <http://creativecommons.org/licenses/by-sa/4.0/>.
"""
from datetime import timedelta
from django.utils import timezone
import datetime
from django.core.exceptions import ValidationError

from django.utils.translation import ugettext_lazy as _


def date_is_present_or_past(value):
    if isinstance(value, datetime.datetime):
        if value > timezone.now():
            raise ValidationError(_("The date entered must be today or lesser."))
    else:
        raise ValidationError(_("The value entered isn't a valid type of date or datetime."))


def logged_time_is_positive(value):
    if isinstance(value, timedelta):
        if value <= timedelta(seconds=0):
            raise ValidationError(_("The logged time must be at least one minute"))
    else:
        raise ValidationError(_("The value entered isn't a valid type of timedelta."))

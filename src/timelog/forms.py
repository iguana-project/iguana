"""
Iguana (c) by Marc Ammon, Moritz Fickenscher, Lukas Fridolin,
Michael Gunselmann, Katrin Raab, Christian Strate

Iguana is licensed under a
Creative Commons Attribution-ShareAlike 4.0 International License.

You should have received a copy of the license along with this
work. If not, see <http://creativecommons.org/licenses/by-sa/4.0/>.
"""
from django.forms import Field, ModelForm, ValidationError, Widget
from django.forms.utils import flatatt, to_current_timezone
from django.utils.html import conditional_escape, format_html, html_safe

from datetimewidget.widgets import DateTimeWidget
from datetime import timedelta
import re

from .models import Timelog
from issue.models import Issue

from django.utils.translation import ugettext_lazy as _

duration_field_help_text = _('e.g. 1d2h10m')


class TimelogCreateForm(ModelForm):
    def __init__(self, *args, **kwargs):
        super(TimelogCreateForm, self).__init__(*args, **kwargs)
        self.fields['time'] = DurationField(help_text=duration_field_help_text)

    class Meta:
        model = Timelog
        fields = ('time', 'created_at')
        widgets = {
            # Use localization and bootstrap 3
            'created_at': DateTimeWidget(attrs={'id': "created_at"}, usel10n=True, bootstrap_version=3),
                }


class TimelogCreateForm2(ModelForm):
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super(TimelogCreateForm2, self).__init__(*args, **kwargs)
        self.fields['time'] = DurationField(help_text=duration_field_help_text)
        self.fields['issue'].queryset = Issue.objects.filter(assignee=user, archived=False)

    class Meta:
        model = Timelog
        fields = ('time', 'created_at', 'issue')
        widgets = {
            # Use localization and bootstrap 3
            'created_at': DateTimeWidget(attrs={'id': "created_at"}, usel10n=True, bootstrap_version=3),
        }


class TimelogEditForm(ModelForm):
    def __init__(self, *args, **kwargs):
        super(TimelogEditForm, self).__init__(*args, **kwargs)
        self.fields['time'] = DurationField()

    class Meta:
        model = Timelog
        fields = ['time', 'created_at']
        widgets = {
            # Use localization and bootstrap 3
            'created_at': DateTimeWidget(attrs={'id': "created_at"}, usel10n=True, bootstrap_version=3),
        }


class DurationWidget(Widget):

    input_type = 'text'

    def format_value(self, value):
        ret = ''
        hours = value.seconds // 3600
        minutes = (value.seconds % 3600) // 60
        if value.days > 0:
            ret += str(value.days)+'d '
        if hours > 0:
            ret += str(hours)+'h '
        if minutes > 0:
            ret += str(minutes) + 'm'
        return ret.strip()

    def render(self, name, value, attrs=None):
        if value is None:
            value = ''
        final_attrs = self.build_attrs(attrs, {'name': name, 'type': self.input_type})
        if isinstance(value, timedelta):
            final_attrs['value'] = self.format_value(value)
        return format_html('<input{} />', flatatt(final_attrs))


class DurationField(Field):
    widget = DurationWidget

    def __init__(self, max_length=None, min_length=None, strip=True, *args, **kwargs):
        super(DurationField, self).__init__(*args, **kwargs)

    def to_python(self, value):
        regex = re.compile(r'((?P<days>\d+?)d\s?)?((?P<hours>\d+?)h\s?)?((?P<minutes>\d+?)m)?')

        def parse_time(time_str):
            if not time_str:
                return None
            parts = regex.fullmatch(time_str)
            if not parts:
                raise ValidationError(_('Invalid time syntax, try e.g "3h5m" or "1h 20m" or "2d15m"'))
            parts = parts.groupdict()
            time_params = {}
            for name, param in parts.items():
                if param:
                    time_params[name] = int(param)
            return timedelta(**time_params)
        return parse_time(value)

    def widget_attrs(self, widget):
        attrs = super(DurationField, self).widget_attrs(widget)

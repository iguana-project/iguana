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
from django.forms import Field, ModelForm, ValidationError

from datetime import timedelta
import re

from .models import Timelog
from issue.models import Issue

from django.utils.translation import ugettext_lazy as _
from timelog.widgets import DurationWidget
from common.widgets import LocalizedDateTimePickerInput

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
            'created_at': LocalizedDateTimePickerInput(attrs={'id': "created_at"}),
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
            'created_at': LocalizedDateTimePickerInput(attrs={'id': "created_at"}),
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
            'created_at': LocalizedDateTimePickerInput(attrs={'id': "created_at"}),
        }


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

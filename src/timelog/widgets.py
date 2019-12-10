"""
Iguana (c) by Marc Ammon, Moritz Fickenscher, Lukas Fridolin,
Michael Gunselmann, Katrin Raab, Christian Strate

Iguana is licensed under a
Creative Commons Attribution-ShareAlike 4.0 International License.

You should have received a copy of the license along with this
work. If not, see <http://creativecommons.org/licenses/by-sa/4.0/>.
"""
from django.forms.widgets import Widget
from datetime import timedelta
from django.utils.html import format_html
from django.forms.utils import flatatt


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

    def render(self, name, value, attrs=None, renderer=None):
        if value is None:
            value = ''
        final_attrs = self.build_attrs(attrs, {'type': self.input_type, 'name': name})

        if isinstance(value, timedelta):
            final_attrs['value'] = self.format_value(value)
        return format_html('<input{} />', flatatt(final_attrs))

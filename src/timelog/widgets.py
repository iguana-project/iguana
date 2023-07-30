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

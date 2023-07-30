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
from django.forms import ModelForm, ValidationError
from sprint.models import Sprint

from django.utils.translation import ugettext_lazy as _
from common.widgets import LocalizedDateTimePickerInput


class SprintForm(ModelForm):
    class Meta:
        model = Sprint
        fields = ['plandate']

        widgets = {
            'startdate': LocalizedDateTimePickerInput(attrs={'id': "startdate"}),
            'enddate': LocalizedDateTimePickerInput(attrs={'id': "enddate"}),
            'plandate': LocalizedDateTimePickerInput(attrs={'id': "plandate"}),
        }

    # verify that startdate < enddate
    # TODO TESTCASE write tests for that
    def clean(self):
        cleaned_data = super(ModelForm, self).clean()

        startdate = cleaned_data.get('startdate')
        enddate = cleaned_data.get('enddate')
        plandate = cleaned_data.get('plandate')
        if startdate and enddate and startdate > enddate:
            raise ValidationError(_("The startdate is prior the enddate, which is not allowed," +
                                    " since this doesn't make any sense at all."))
        if startdate and plandate and startdate > plandate:
            raise ValidationError(_("The startdate is prior the planned enddate, which is not allowed," +
                                    " since this doesn't make any sense at all."))

        return cleaned_data

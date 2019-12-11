"""
Iguana (c) by Marc Ammon, Moritz Fickenscher, Lukas Fridolin,
Michael Gunselmann, Katrin Raab, Christian Strate

Iguana is licensed under a
Creative Commons Attribution-ShareAlike 4.0 International License.

You should have received a copy of the license along with this
work. If not, see <http://creativecommons.org/licenses/by-sa/4.0/>.
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

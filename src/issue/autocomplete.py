"""
Iguana (c) by Marc Ammon, Moritz Fickenscher, Lukas Fridolin,
Michael Gunselmann, Katrin Raab, Christian Strate

Iguana is licensed under a
Creative Commons Attribution-ShareAlike 4.0 International License.

You should have received a copy of the license along with this
work. If not, see <http://creativecommons.org/licenses/by-sa/4.0/>.
"""
from common.views import AutoCompleteView
from issue.models import Issue


class IssuePrioAutocompleteView(AutoCompleteView):
    def get_queryset(self):
        if not self.request.user.is_authenticated:
            return []

        qs = Issue.PRIORITY_TYPES

        if self.q:
            qs = [prio_type for prio_type in qs if self.q in prio_type[1].lower()]

        return qs

    def get_result_label_html(self, result):
        if result[0] == 4:
            return '<span class="glyphicon glyphicon-arrow-up red"></span>'\
                '<span style="padding-left: .5em">%s</span>' % result[1]
        if result[0] == 3:
            return '<span class="glyphicon glyphicon-arrow-up gly-rotate-45 red"></span>'\
                '<span style="padding-left: .5em">%s</span>' % result[1]
        if result[0] == 2:
            return '<span class="glyphicon glyphicon-arrow-up gly-rotate-90 yellow"></span>'\
                '<span style="padding-left: .5em">%s</span>' % result[1]
        if result[0] == 1:
            return '<span class="glyphicon glyphicon-arrow-up gly-rotate-145 green"></span>'\
                '<span style="padding-left: .5em">%s</span>' % result[1]
        if result[0] == 0:
            return '<span class="glyphicon glyphicon-arrow-up gly-rotate-180 green"></span>'\
                '<span style="padding-left: .5em">%s</span>' % result[1]

    def get_result_label_clean(self, result):
        return str(result[0])

    def get_result_value(self, result):
        return result[0]

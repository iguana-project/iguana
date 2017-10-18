"""
Iguana (c) by Marc Ammon, Moritz Fickenscher, Lukas Fridolin,
Michael Gunselmann, Katrin Raab, Christian Strate

Iguana is licensed under a
Creative Commons Attribution-ShareAlike 4.0 International License.

You should have received a copy of the license along with this
work. If not, see <http://creativecommons.org/licenses/by-sa/4.0/>.
"""
from django.forms import ModelForm
from search.models import Search
from dal import autocomplete


class SearchEditForm(ModelForm):
    class Meta:
        model = Search
        fields = ('description', 'searchexpression', 'shared_with', 'persistent')
        widgets = {
                'shared_with': autocomplete.ModelSelect2Multiple('search:projectac', attrs={'data-html': 'true'})
        }

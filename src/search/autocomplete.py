"""
Iguana (c) by Marc Ammon, Moritz Fickenscher, Lukas Fridolin,
Michael Gunselmann, Katrin Raab, Christian Strate

Iguana is licensed under a
Creative Commons Attribution-ShareAlike 4.0 International License.

You should have received a copy of the license along with this
work. If not, see <http://creativecommons.org/licenses/by-sa/4.0/>.
"""
from dal import autocomplete
from django.contrib.auth import get_user_model
from django.db.models import Q
from project.models import Project


class ProjectAutocompleteView(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        if not self.request.user.is_authenticated:
            return get_user_model().objects.none()

        u = self.request.user
        return Project.objects.filter(Q(developer=u) | Q(manager=u))

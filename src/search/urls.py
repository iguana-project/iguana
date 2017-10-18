"""
Iguana (c) by Marc Ammon, Moritz Fickenscher, Lukas Fridolin,
Michael Gunselmann, Katrin Raab, Christian Strate

Iguana is licensed under a
Creative Commons Attribution-ShareAlike 4.0 International License.

You should have received a copy of the license along with this
work. If not, see <http://creativecommons.org/licenses/by-sa/4.0/>.
"""
from django.conf.urls import url

from search import views
from .autocomplete import ProjectAutocompleteView

app_name = 'search'

urlpatterns = [
    url(r'^$', views.SearchView.as_view(), name='search'),
    url(r'^result/?$', views.ResultView.as_view(), name='resultpage'),
    url(r'^advanced/?$', views.AdvancedSearchView.as_view(), name='advanced'),
    url(r'^advanced/edit/(?P<sqn_sh>[0-9]+)/?$', views.SearchEditView.as_view(), name='edit'),
    url(r'^projectac/?$', ProjectAutocompleteView.as_view(), name='projectac'),
    url(r'^makepersistent/?$', views.MakeSearchPersistentView.as_view(), name='makepersistent'),
    url(r'^delpersistent/?$', views.DelSearchPersistentView.as_view(), name='delpersistent'),
]

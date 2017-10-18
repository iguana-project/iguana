"""
Iguana (c) by Marc Ammon, Moritz Fickenscher, Lukas Fridolin,
Michael Gunselmann, Katrin Raab, Christian Strate

Iguana is licensed under a
Creative Commons Attribution-ShareAlike 4.0 International License.

You should have received a copy of the license along with this
work. If not, see <http://creativecommons.org/licenses/by-sa/4.0/>.
"""
from django.conf.urls import url, include

from gitintegration import views

app_name = 'gitintegration'

# included from project/urls.py
urlpatterns = [
    url(r'^$', views.RepositoryListView.as_view(), name='list'),
    url(r'^create/?$', views.RepositoryCreateView.as_view(), name='create'),
    url(r'(?P<repository>[0-9]+)/', include([
        url(r'^$', views.RepositoryDetailView.as_view(), name='detail'),
        url(r'^edit/?$', views.RepositoryEditView.as_view(), name='edit'),
        url(r'^delete/?$', views.RepositoryDeleteView.as_view(), name='delete'),
    ]))
]

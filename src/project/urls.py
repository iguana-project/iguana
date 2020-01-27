"""
Iguana (c) by Marc Ammon, Moritz Fickenscher, Lukas Fridolin,
Michael Gunselmann, Katrin Raab, Christian Strate

Iguana is licensed under a
Creative Commons Attribution-ShareAlike 4.0 International License.

You should have received a copy of the license along with this
work. If not, see <http://creativecommons.org/licenses/by-sa/4.0/>.
"""
from django.conf.urls import url, include
from django.contrib.auth import views as auth_views
from project import views
from search import views as se_views
from common.urls import project_pattern, project_pattern_optional
from .autocomplete import *

app_name = 'project'

urlpatterns = [
    url(r'^$', views.ProjectListAllView.as_view(), name='list'),
    url(r'^create/?$', views.ProjectCreateView.as_view(), name='create'),
    url(r'^userac/?'+project_pattern_optional+r'/?$', UserAutocompleteView.as_view(), name='userac'),
    url(r'^issueac/'+project_pattern+r'(?P<issue>[0-9]+)?/?$', IssueAutocompleteView.as_view(), name='issueac'),
    url(r'^tagac/'+project_pattern_optional+r'/?$', TagAutocompleteView.as_view(), name='tagac'),
    url(r'^kanbanac/'+project_pattern_optional+r'/?$', KanbanAutocompleteView.as_view(), name='kanbanac'),
    url(project_pattern, include([
        url(r'^detail/?$', views.ProjectDetailView.as_view(), name='detail'),
        url(r'^timelog/?$', views.ProjectDetailTimelogView.as_view(), name='timelog'),
        url(r'^timelog/(?P<username>[a-zA-Z0-9_+\.-]+)/?$',
            views.ProjectUserTimelogView.as_view(),
            name='usertimelog'),
        url(r'^edit/?$', views.ProjectEditView.as_view(), name='edit'),
        url(r'^delete/?$', views.ProjectDeleteView.as_view(), name='delete'),
        url(r'^filter/?$', se_views.ProjectFilterView.as_view(), name='search'),
        url(r'^repository/', include('gitintegration.urls')),
        url(r'^leave/', views.LeaveProjectView.as_view(), name='leave'),
    ]))
]

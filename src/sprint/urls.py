"""
Iguana (c) by Marc Ammon, Moritz Fickenscher, Lukas Fridolin,
Michael Gunselmann, Katrin Raab, Christian Strate

Iguana is licensed under a
Creative Commons Attribution-ShareAlike 4.0 International License.

You should have received a copy of the license along with this
work. If not, see <http://creativecommons.org/licenses/by-sa/4.0/>.
"""
from django.conf.urls import url

from sprint import views

app_name = 'sprint'


sprint_sqn_s_pattern = r'(?P<sqn_s>[0-9]+)'

urlpatterns = [
    url(r'^$', views.SprintboardView.as_view(), name='sprintboard'),
    url(r'^newsprint/?$', views.NewSprintView.as_view(), name='newsprint'),
    url(r'^editsprint/'+sprint_sqn_s_pattern+r'/?$', views.SprintEditView.as_view(), name='editsprint'),
    # NOTE WARNING: this page is broken because of the errors described in the relative template
    #      the WHOLE PROJECT WILL BE DELETED!!! NOTE DON'T REACTIVATE WITHOUT FIX!!!!!!!!!!!!
    # url(r'^deletesprint/'+sprint_sqn_s_pattern+r'/?$', views.Sprint_Delete_View.as_view(), name='deletesprint'),
    url(r'toggletofromsprint/?$', views.ToggleIssueToFromSprintView.as_view(), name='assigntosprint',),
    url(r'^startsprint/'+sprint_sqn_s_pattern+r'/?$', views.StartSprintView.as_view(), name='startsprint'),
    url(r'^stopsprint/'+sprint_sqn_s_pattern+r'/?$', views.StopSprintView.as_view(), name='stopsprint'),
]

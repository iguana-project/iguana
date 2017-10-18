"""
Iguana (c) by Marc Ammon, Moritz Fickenscher, Lukas Fridolin,
Michael Gunselmann, Katrin Raab, Christian Strate

Iguana is licensed under a
Creative Commons Attribution-ShareAlike 4.0 International License.

You should have received a copy of the license along with this
work. If not, see <http://creativecommons.org/licenses/by-sa/4.0/>.
"""
from django.conf.urls import url
from timelog import views, json
app_name = 'timelog'

urlpatterns = [
    url(r'^$', views.TimelogLoginfoPerUserView.as_view(), name='loginfo'),
    # url(r'^lastseven/$', views.Timelog_chartjs.as_view(), name='last7days'),
    url(r'^lastweek/$', views.TimelogD3View.as_view(), name='d3'),
    url(r'^activity/$', views.TimelogGetActivityDataView.as_view(), name='activity'),
    url(r'^logs/$', views.TimelogArchivView.as_view(), name='archiv'),
    url(r'^api/last_7_days/?$', json.d3_json_last_7_days, name='api_last_7_days'),
    url(r'^api/activity/?$', json.d3_json_activity, name='api_activity'),
    url(r'^api/project_activity/?$', json.get_activity_data_for_project, name='api_project_activity'),
    url(r'^api/(?P<date>[0-9]+)?/?', json.d3_json_logs_specific_day, name='api_logs_on_date'),
]

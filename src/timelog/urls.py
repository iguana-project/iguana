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

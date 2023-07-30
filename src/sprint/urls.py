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

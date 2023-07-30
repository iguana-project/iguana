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
from django.conf.urls import url, include
from django.contrib.auth import views as auth_views
from project import views
from search import views as se_views
from common.urls import project_pattern, project_pattern_optional, issue_pattern_optional
from .autocomplete import *

app_name = 'project'

urlpatterns = [
    url(r'^$', views.ProjectListAllView.as_view(), name='list'),
    url(r'^create/?$', views.ProjectCreateView.as_view(), name='create'),
    url(r'^userac/?'+project_pattern_optional+r'/?$', UserAutocompleteView.as_view(), name='userac'),
    url(r'^issueac/'+project_pattern+issue_pattern_optional+r'?$', IssueAutocompleteView.as_view(), name='issueac'),
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

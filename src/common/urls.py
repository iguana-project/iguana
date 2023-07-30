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
from django.contrib import admin
from django.conf.urls.i18n import i18n_patterns
from django.conf import settings
from django.conf.urls.static import static


from common import views

app_name = 'common'


project_pattern = r'(?P<project>[0-9a-zA-Z]{1,4})/'
project_pattern_optional = r'(?P<project>[0-9a-zA-Z]{1,4})?'
issue_pattern = r'(?P<issue>[0-9]+)/'
issue_pattern_optional = r'(?P<issue>[0-9]+)?/'

urlpatterns = [
    url(r'^', include('landing_page.urls')),
    url(r'^', include('user_management.urls')),
    url(r'^',
        include(([url(r'^filter_create/$', views.CreateFilterView.as_view(), name='create_filter'), ],
                 'common'))),
    url(r'^captcha/', include('captcha.urls')),
    url(r'^invite/', include('invite_users.urls')),
    url(r'^project/', include('project.urls')),
    url(r'^project/'+project_pattern, include('archive.urls')),
    url(r'^project/'+project_pattern, include('backlog.urls')),
    url(r'^project/'+project_pattern, include('olea.urls')),
    url(r'^project/'+project_pattern, include('sprint.urls')),
    url(r'^project/'+project_pattern+r'column/', include('kanbancol.urls')),
    url(r'^project/'+project_pattern+r'integration/', include('integration.urls')),
    url(r'^', include('issue.urls')),
    url(r'^project/'+project_pattern+r'tag/', include('tag.urls')),
    url(r'^search/', include('search.urls')),
    url(r'^timelog/', include('timelog.urls')),
    url(r'^user/', include('user_profile.urls')),
    url(r'^', include('discussion.urls')),
    url(r'^media/.*', views.ShowProtectedFilesView.as_view()),
    url(r'^api/', include('api.urls', namespace='api')),
]


# enable the admin interface by request
if settings.ADMIN_ENABLED:
    urlpatterns.append(url(r'^admin/', admin.site.urls))

# this is needed to load the media files in the built-in django server
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

"""
Iguana (c) by Marc Ammon, Moritz Fickenscher, Lukas Fridolin,
Michael Gunselmann, Katrin Raab, Christian Strate

Iguana is licensed under a
Creative Commons Attribution-ShareAlike 4.0 International License.

You should have received a copy of the license along with this
work. If not, see <http://creativecommons.org/licenses/by-sa/4.0/>.
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

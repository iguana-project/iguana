"""
Iguana (c) by Marc Ammon, Moritz Fickenscher, Lukas Fridolin,
Michael Gunselmann, Katrin Raab, Christian Strate

Iguana is licensed under a
Creative Commons Attribution-ShareAlike 4.0 International License.

You should have received a copy of the license along with this
work. If not, see <http://creativecommons.org/licenses/by-sa/4.0/>.
"""
from django.conf.urls import url, include

from backlog import views
from common.urls import project_pattern

app_name = 'backlog'


sprint_sqn_s_pattern = r'(?P<sqn_s>[0-9]+)'

urlpatterns = [
    url(r'backlog/?$', views.BacklogListView.as_view(), name='backlog'),
    url(r'^backlog/'+sprint_sqn_s_pattern+r'/?$', views.BacklogListView.as_view(), name='backlog'),
]

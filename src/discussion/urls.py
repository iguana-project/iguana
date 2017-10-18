"""
Iguana (c) by Marc Ammon, Moritz Fickenscher, Lukas Fridolin,
Michael Gunselmann, Katrin Raab, Christian Strate

Iguana is licensed under a
Creative Commons Attribution-ShareAlike 4.0 International License.

You should have received a copy of the license along with this
work. If not, see <http://creativecommons.org/licenses/by-sa/4.0/>.
"""
from django.conf.urls import url, include

from discussion import views

from common.urls import project_pattern

app_name = "discussion"

urlpatterns = [
    url(r'^discussion/', include([
        url(r'^$', views.DiscussionsView.as_view(), name='list'),
    ])),
    url(r'^project/'+project_pattern+r'issue/', include([
        url(r'^seen/?$', views.SeenView.as_view(), name='seen'),
        url(r'^(?P<sqn_i>[0-9]+)/', include([
            url(r'^mute/?$', views.MuteView.as_view(), name='mute'),
            url(r'^follow/?$', views.FollowView.as_view(), name='follow'),
        ])),
    ]))
]

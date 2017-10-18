"""
Iguana (c) by Marc Ammon, Moritz Fickenscher, Lukas Fridolin,
Michael Gunselmann, Katrin Raab, Christian Strate

Iguana is licensed under a
Creative Commons Attribution-ShareAlike 4.0 International License.

You should have received a copy of the license along with this
work. If not, see <http://creativecommons.org/licenses/by-sa/4.0/>.
"""
from django.conf.urls import url, include

from integration import views

app_name = 'integration'

slack_patterns = ([
    url(r'^auth/?$', views.SlackIntegrationOAuthView.as_view(), name='auth'),
    url(r'^(?P<pk>[0-9]+)/', include([
        url(r'^$', views.SlackIntegrationUpdateView.as_view(), name='update'),
        url(r'^delete/?$', views.SlackIntegrationDeleteView.as_view(), name='delete'),
    ])),
], 'slack')

urlpatterns = [
    url(r'^slack/', include(slack_patterns, namespace='slack'))
]

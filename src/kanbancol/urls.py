"""
Iguana (c) by Marc Ammon, Moritz Fickenscher, Lukas Fridolin,
Michael Gunselmann, Katrin Raab, Christian Strate

Iguana is licensed under a
Creative Commons Attribution-ShareAlike 4.0 International License.

You should have received a copy of the license along with this
work. If not, see <http://creativecommons.org/licenses/by-sa/4.0/>.
"""
from django.conf.urls import url, include

from kanbancol import views


app_name = 'kanbancol'

urlpatterns = [
    url(r'^create/?$', views.KanbanColumnCreateView.as_view(), name='create'),
    url(r'^(?P<position>[0-9]+)/', include([
        url(r'^$', views.KanbanColumnBreadcrumbView.as_view()),
        url(r'^update/?$', views.KanbanColumnUpdateView.as_view(), name='update'),
        url(r'^delete/?$', views.KanbanColumnDeleteView.as_view(), name='delete'),
        url(r'^moveup/?$', views.KanbanColumnUpView.as_view(), name='moveup'),
        url(r'^movedown/?$', views.KanbanColumnDownView.as_view(), name='movedown'),
    ]))
]

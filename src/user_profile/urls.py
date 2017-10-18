"""
Iguana (c) by Marc Ammon, Moritz Fickenscher, Lukas Fridolin,
Michael Gunselmann, Katrin Raab, Christian Strate

Iguana is licensed under a
Creative Commons Attribution-ShareAlike 4.0 International License.

You should have received a copy of the license along with this
work. If not, see <http://creativecommons.org/licenses/by-sa/4.0/>.
"""
from django.conf.urls import url, include
from user_profile import views
from common.views import BreadcrumbView


app_name = 'user_profile'

urlpatterns = [
    url(r'^$', BreadcrumbView.as_view(breadcrumb="Profile")),
    url(r'^(?P<username>[a-zA-Z0-9_+\.-]+)/', include([
        url(r'^$', views.ShowProfilePageView.as_view(), name='user_profile_page'),
        url(r'^edit/?$', views.EditProfilePageView.as_view(), name='edit_profile'),
        url(r'^notify/?$', views.ToggleNotificationView.as_view(), name='toggle_notification'),
    ]))
]

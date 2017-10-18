"""
Iguana (c) by Marc Ammon, Moritz Fickenscher, Lukas Fridolin,
Michael Gunselmann, Katrin Raab, Christian Strate

Iguana is licensed under a
Creative Commons Attribution-ShareAlike 4.0 International License.

You should have received a copy of the license along with this
work. If not, see <http://creativecommons.org/licenses/by-sa/4.0/>.
"""
from django.conf.urls import url
from invite_users import views

app_name = 'invite_users'

urlpatterns = [
    url(r'^$', views.InviteUserView.as_view(), name='invite_users'),
    url(r'^invite_users/?$', views.InviteUserView.as_view(), name='invite_users'),
    url(r'^successfully_invited/?$', views.SuccessView.as_view(), name='successfully_invited'),
]

"""
Iguana (c) by Marc Ammon, Moritz Fickenscher, Lukas Fridolin,
Michael Gunselmann, Katrin Raab, Christian Strate

Iguana is licensed under a
Creative Commons Attribution-ShareAlike 4.0 International License.

You should have received a copy of the license along with this
work. If not, see <http://creativecommons.org/licenses/by-sa/4.0/>.
"""
from django.conf.urls import url, include
from user_management import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    # user-id/timestamp-generated_token
    url(r'^activate/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/?$',
        views.VerifyEmailAddress.as_view(), name='verify_email'),
    url(r'^sign_up/?$', views.SignUpView.as_view(), name='sign_up'),
    url(r'^sign-up/?$', views.SignUpView.as_view(), name='sign_up'),
    url(r'^register/?$', views.SignUpView.as_view(), name='sign_up'),
    url(r'^login/?$', views.LoginView.as_view(), name='login'),
    url(r'^logout/?$', views.LogoutView.as_view(), name='logout'),
    # NOTE: the password_reset-views don't work as expected yet
    #       it seems like there is a bug in django
    # TODO BUG is this still an issue?
    url(r'^password_reset/$', views.PasswordResetView.as_view(), name='password_reset'),
    url('^', include('django.contrib.auth.urls')),
    url(r'^password_reset/done$', views.PasswordResetSuccessView.as_view(), name='password_reset_done'),
]

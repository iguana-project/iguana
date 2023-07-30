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

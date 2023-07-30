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
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView
from django.conf import settings
import hashlib
from rest_framework_simplejwt.tokens import AccessToken
from rest_framework_simplejwt.settings import api_settings
from django.contrib.auth import get_user_model
from django.utils.translation import ugettext_lazy as _
from rest_framework_simplejwt.exceptions import TokenError


PASSWORD_HASH_CLAIM = "user_valid"


def get_current_password_hash(user):
    """
    This method creates an individual hash based on the user's current password hash
    and the current SECRET_KEY.
    """
    hash_string = user.password + settings.SECRET_KEY
    return hashlib.sha256(hash_string.encode("utf-8")).hexdigest()


class AccessTokenWithUserValidation(AccessToken):
    def verify(self):
        AccessToken.verify(self)

        # get the user of this token
        user_id = self[api_settings.USER_ID_CLAIM]
        user = get_user_model().objects.get(id=user_id)

        # calculate the current password hash for validation
        valid_hash = get_current_password_hash(user)
        # compare the stored hash with the just calculated one
        if self[PASSWORD_HASH_CLAIM] != valid_hash:
            raise TokenError(_("Token is invalid or expired"))


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        # add a custom claim with the user's current password hash
        token[PASSWORD_HASH_CLAIM] = get_current_password_hash(user)

        return token


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

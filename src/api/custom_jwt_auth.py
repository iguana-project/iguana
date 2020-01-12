"""
Iguana (c) by Marc Ammon, Moritz Fickenscher, Lukas Fridolin,
Michael Gunselmann, Katrin Raab, Christian Strate

Iguana is licensed under a
Creative Commons Attribution-ShareAlike 4.0 International License.

You should have received a copy of the license along with this
work. If not, see <http://creativecommons.org/licenses/by-sa/4.0/>.
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

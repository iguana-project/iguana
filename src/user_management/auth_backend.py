"""
Iguana (c) by Marc Ammon, Moritz Fickenscher, Lukas Fridolin,
Michael Gunselmann, Katrin Raab, Christian Strate

Iguana is licensed under a
Creative Commons Attribution-ShareAlike 4.0 International License.

You should have received a copy of the license along with this
work. If not, see <http://creativecommons.org/licenses/by-sa/4.0/>.
"""
from django.contrib.auth import get_user_model

"""
Inspired by
 - http://blackglasses.me/2013/10/08/custom-django-user-model-part-2/
 - http://www.jaco.it/blog/2013/04/05/custom-django-auth-to-login-with-email
"""


# Provides the possibility to login with username or email
class AuthBackend(object):
    User = get_user_model()

    def get_user(self, user_id):
        try:
            return self.User.objects.get(pk=user_id)
        except self.User.DoesNotExist:
            return None

    def authenticate(self, username=None, password=None):
        if username is None or password is None:
            return None

        try:
            if '@' in username:
                user = self.User.objects.get(email=username)
            else:
                user = self.User.objects.get(username=username)
        except self.User.DoesNotExist:
            return None

        if user.check_password(password):
            return user

        return None

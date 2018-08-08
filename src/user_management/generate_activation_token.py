from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils import six


# used to generate email verification tokens - they have to match the scheme of the check_token()
# s.a. https://simpleisbetterthancomplex.com/tutorial/2016/08/24/how-to-create-one-time-link.html
class AccountActivationTokenGenerator(PasswordResetTokenGenerator):
    # the url itself is generated with this hash in combination with the platform-secret
    # and a specific salted hash
    def _make_hash_value(self, user, timestamp):
        return six.text_type(user.id) + six.text_type(timestamp) + six.text_type(user.is_active)


account_activation_token = AccountActivationTokenGenerator()

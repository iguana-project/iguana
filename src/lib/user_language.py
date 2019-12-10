"""
Iguana (c) by Marc Ammon, Moritz Fickenscher, Lukas Fridolin,
Michael Gunselmann, Katrin Raab, Christian Strate

Iguana is licensed under a
Creative Commons Attribution-ShareAlike 4.0 International License.

You should have received a copy of the license along with this
work. If not, see <http://creativecommons.org/licenses/by-sa/4.0/>.
"""
from cuser.middleware import CuserMiddleware
from django.utils.functional import lazy, Promise
from django.utils.translation import to_locale
from common import settings
from django.core.serializers.json import DjangoJSONEncoder
from django.utils.encoding import force_text
import json


"""
This JSON encoder is needed for encoding lazy objects (mostly translated language strings)
"""


class LazyEncoder(DjangoJSONEncoder):
    def default(self, obj):
        if isinstance(obj, Promise):
            return force_text(obj)
        return super(LazyEncoder, self).default(obj)


# register the encoder as the default one
json._default_encoder = LazyEncoder(
    skipkeys=False,
    ensure_ascii=True,
    check_circular=True,
    allow_nan=True,
    indent=None,
    separators=None,
    default=None,
)


"""
Helper methods for getting the current user's language or locale setting.
"""


def get_user_language():
    user = CuserMiddleware.get_user()
    if user is None:
        return settings.LANGUAGE_CODE
    else:
        return user.language


get_user_language_lazy = lazy(get_user_language, str)


def get_user_locale():
    lang = get_user_language()
    return to_locale(lang)


get_user_locale_lazy = lazy(get_user_locale, str)

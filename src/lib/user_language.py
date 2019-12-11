"""
Iguana (c) by Marc Ammon, Moritz Fickenscher, Lukas Fridolin,
Michael Gunselmann, Katrin Raab, Christian Strate

Iguana is licensed under a
Creative Commons Attribution-ShareAlike 4.0 International License.

You should have received a copy of the license along with this
work. If not, see <http://creativecommons.org/licenses/by-sa/4.0/>.
"""
from cuser.middleware import CuserMiddleware
from django.utils.functional import lazy
from django.utils.translation import to_locale
from django.conf import settings
from django.utils import formats


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


# PHP datetime format => python datetime format
# this is needed because django.utils.formats works with the PHP format
php_py_format_map = (
    ('z', r'%j'),
    ('d', r'%d'),
    ('F', r'%B'),
    ('M', r'%b'),
    ('m', r'%m'),
    ('Y', r'%Y'),
    ('y', r'%y'),
    ('H', r'%H'),
    ('h', r'%I'),
    ('i', r'%M'),
    ('s', r'%S'),
    ('a', r'%p'),
    ('O', r'%z'),
    ('P', r'%I:%M %p'),
)


def get_user_locale_format(format_key):
    lang = get_user_language()
    frmat = formats.get_format(format_key, lang=lang, use_l10n=True)
    for php_format, py_format in php_py_format_map:
        frmat = frmat.replace(php_format, py_format)
    return frmat


get_user_locale_format_lazy = lazy(get_user_locale_format, str)

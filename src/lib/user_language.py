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

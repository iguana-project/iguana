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
from random import SystemRandom
import string
import json
from collections import OrderedDict
import os


# the base directory is relative 3 directories up to this file
BASE_DIR = os.path.abspath(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))


# the settings files that are configured by this script
IGUANA_SETTINGS_FILE = os.path.join(BASE_DIR, "files", "settings.json")
DJANGO_SETTINGS_FILE = os.path.join(BASE_DIR, "src", "common", "settings", "__init__.py")


def initialize_secret_key(is_development_mode, override=False):
    """
    Initialize the secret key in the django settings.

    Set 'override=True' to force the creation of a new secret key.
    """
    # generate a secret key for django; this is needed
    secret_key = ''.join([SystemRandom().choice(string.digits + string.ascii_uppercase + string.ascii_lowercase +
                                                '!@#$%^&*(-_=+)')
                          for _ in range(50)])

    # advise django to use the right settings file
    with open(DJANGO_SETTINGS_FILE, 'w+') as f:
        if is_development_mode:
            # do not override the secret key by default
            if "SECRET_KEY" not in f.read() or override:
                f.write("from .local_conf import *")
                f.write('\n\n')
                f.write("SECRET_KEY = \"" + secret_key + "\"")
                f.write('\n')
        else:
            f.write("from .global_conf import *")
            f.write('\n')

        f.close()

    # initialize the Iguana settings file if not in development mode
    if not is_development_mode:
        with open(IGUANA_SETTINGS_FILE, 'r') as f:
            global_settings = json.load(f, object_pairs_hook=OrderedDict)
            f.close()

        # do not override an already set value
        if global_settings["django"]["required_settings"]["SECRET_KEY"] == "#### Change ME!!! ####" or \
                override:
            global_settings["django"]["required_settings"]["SECRET_KEY"] = secret_key

            with open(IGUANA_SETTINGS_FILE, 'w') as f:
                json.dump(global_settings, f, indent=4)
                f.close()


def set_django_settings(is_development_mode, settings={}, quote_values=True):
    """
    Add/set one or more settings to
        <application_root>/files/settings.json (for production/staging) OR
        <application_root>/src/common/settings/__init__.py (for development)
    settings file.

    Set 'quote_values=False' if the values should be interpreted as python code (only possible in development mode).
    """
    if is_development_mode:
        # if landing here the settings file is not a json file
        # so open it as a normal text file
        with open(DJANGO_SETTINGS_FILE, 'a') as f:
            for key, value in settings.items():
                if quote_values:
                    f.write(str(key) + " = \"" + str(value) + "\"")
                else:
                    f.write(str(key) + " = " + str(value))
                f.write('\n')

            f.close()
    else:
        with open(IGUANA_SETTINGS_FILE, 'r') as f:
            global_settings = json.load(f, object_pairs_hook=OrderedDict)
            f.close()

        for key, value in settings.items():
            setting = _find_item_in_dict(global_settings, key)

            # continue if no setting was found
            if not setting:
                continue

            # set the setting
            setting[key] = value

        with open(IGUANA_SETTINGS_FILE, 'w') as f:
            # write the changing to file
            json.dump(global_settings, f, indent=4)
            f.close()


def _find_item_in_dict(dictionary, key):
    """
    Helper method to check recursively if a key is in a dictionary.
    Returns the dictionary that contains the key.
    """
    if key in dictionary:
        return dictionary

    for value in dictionary.values():
        if isinstance(value, dict):
            item = _find_item_in_dict(value, key)
            if item is not None:
                return item

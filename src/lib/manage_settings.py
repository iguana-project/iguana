"""
Iguana (c) by Marc Ammon, Moritz Fickenscher, Lukas Fridolin,
Michael Gunselmann, Katrin Raab, Christian Strate

Iguana is licensed under a
Creative Commons Attribution-ShareAlike 4.0 International License.

You should have received a copy of the license along with this
work. If not, see <http://creativecommons.org/licenses/by-sa/4.0/>.
"""
from random import SystemRandom
import string
import json
from collections import OrderedDict


def initialize_secret_key(django_settings_file, iguana_settings_file, is_development_mode, override=False):
    """
    Initialize the secret key in the django settings.

    Set 'override=True' to force the creation of a new secret key.
    """
    # generate a secret key for django; this is needed
    secret_key = ''.join([SystemRandom().choice(string.digits + string.ascii_uppercase
                                                + string.ascii_lowercase + '!@#$%^&*(-_=+)')
                          for _ in range(50)])

    # advise django to use the right settings file
    with open(django_settings_file, 'w+') as f:
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
        with open(iguana_settings_file, 'r') as f:
            global_settings = json.load(f, object_pairs_hook=OrderedDict)
            f.close()

        # do not override an already set value
        if global_settings["django"]["required_settings"]["SECRET_KEY"] == "#### Change ME!!! ####" or \
                override:
            global_settings["django"]["required_settings"]["SECRET_KEY"] = secret_key

            with open(iguana_settings_file, 'w') as f:
                json.dump(global_settings, f, indent=4)
                f.close()


def set_django_settings(settings_file, settings={}, quote_values=True):
    """
    Add/set one or more settings to the provided settings file.
    It could be either the settings file for production/staging: <application_root>/files/settings.json
    Or for development: <application_root>/src/common/settings/__init__.py

    Set 'quote_values=False' if the values should be interpreted as python code.
    """
    try:
        with open(settings_file, 'r') as f:
            global_settings = json.load(f, object_pairs_hook=OrderedDict)
            f.close()

        for key, value in settings.items():
            setting = _find_item_in_dict(global_settings, key)

            # return if no setting was found
            if not setting:
                return

            # set the setting
            setting[key] = value

        with open(settings_file, 'w') as f:
            # write the changing to file
            json.dump(global_settings, f, indent=4)
            f.close()

        # return because the settings file was a json file
        return
    except Exception:
        pass

    # if landing here the settings file is not a json file
    # so open it as a normal text file
    with open(settings_file, 'a') as f:
        for key, value in settings.items():
            if quote_values:
                f.write(str(value) + " = \"" + str(key) + "\"")
            else:
                f.write(str(value) + " = " + str(key))
            f.write('\n')

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

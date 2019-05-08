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


def initialize_settings(django_settings_file, iguana_settings_file, development_mode, override=False):
    # generate a secret key for django; this is needed
    secret_key = ''.join([SystemRandom().choice(string.digits + string.ascii_uppercase
                                                + string.ascii_lowercase + '!@#$%^&*(-_=+)')
                          for _ in range(50)])

    # advise django to use the right settings file
    with open(django_settings_file, 'r+') as f:
        if development_mode:
            # do not override the secret key by default
            if "SECRET_KEY" not in f.read() or override:
                f.write("from .local_conf import *")
                f.write('\n\n')
                f.write("SECRET_KEY = \"" + secret_key + "\"\n")
        else:
            f.write("from .global_conf import *")

        f.close()

    # initialize the Iguana settings file if not in development mode
    if not development_mode:
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

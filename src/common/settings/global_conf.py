"""
This file contains all settings for running Iguana on a host.
"""

# First import the common settings
from .common import *
import json
import sys


# load the user settings JSON file
# the location is defined in the Ansible scripts
_settings_file = open("/var/lib/iguana/settings/settings.json").read()
_settings = json.loads(_settings_file)


# function to get a setting from the settings.json
def get_setting(names, required=True, default=""):
    missing_req_set = "\033[31mA required setting is missing: \33[34m{}\33[0m".format(" -> ".join(names))
    warning = ("\033[33mWarning - default value for the following settings used:"
               " \33[34m{}\33[0m\n".format(" -> ".join(names)))

    # otherwise the whole settings would be returned
    if(not len(names)):
        raise Exception("\033[31mrequested values for empty keys\33[0m")

    setting = _settings
    for i in range(len(names)):
        # if the value is not required and a default exists there is no need
        # for the relative setting to be in the json file
        try:
            setting = setting[names[i]]
        except KeyError:
            if not required:
                sys.stderr.write(warning)
                return default
            else:
                raise Exception(missing_req_set)

    # catch existing key with empty values
    if required and not setting:
        raise Exception(missing_req_set)
    elif not setting:
        sys.stderr.write(warning)
        return default

    return setting


# The Django secret key
# see https://docs.djangoproject.com/en/1.11/ref/settings/#secret-key
SECRET_KEY = get_setting(["django", "required_settings", "SECRET_KEY"])


# Name of the platform.
# This string is used by several templates.
PLATFORM = get_setting(["django", "optional_settings", "PLATFORM_NAME"], False, PLATFORM)

# The length of the captcha image
CAPTCHA_LENGTH = int(get_setting(["django", "optional_settings", "CAPTCHA_LENGTH"], False, CAPTCHA_LENGTH))

# Language setting
LANGUAGE_CODE = get_setting(["django", "optional_settings", "LANGUAGE_CODE"], False, LANGUAGE_CODE)

# Time zone setting
TIME_ZONE = get_setting(["django", "optional_settings", "TIME_ZONE"], False, TIME_ZONE)


# The host settings
# see https://docs.djangoproject.com/en/1.11/ref/settings/#host
HOST = get_setting(["django", "required_settings", "HOST"])
# see https://docs.djangoproject.com/en/1.11/ref/settings/#std:setting-ALLOWED_HOSTS
ALLOWED_HOSTS = get_setting(["django", "required_settings", "ALLOWED_HOSTS"])


# Admins
# https://docs.djangoproject.com/en/1.11/ref/settings/#admins
ADMINS = [tuple(user) for user in get_setting(["django", "optional_settings", "ADMINS"], False, [])]


# The settings for the database that should be used by django
# Iguana uses a Postgres SQL database
# see https://docs.djangoproject.com/en/1.11/ref/settings/#databases
DATABASES = {
    'default': {
        'ENGINE': "django.db.backends.postgresql_psycopg2",
        'NAME': get_setting(["database", "DATABASE_NAME"]),
        'USER': get_setting(["database", "USER"]),
        'PASSWORD': get_setting(["database", "PASSWORD"]),
        'HOST': get_setting(["database", "HOST"]),
        'PORT': get_setting(["database", "PORT"]),
    }
}


REDIS_URL = get_setting(["redis", "HOST"], False, 'localhost')

CELERY_BROKER_URL = 'redis://'+REDIS_URL+':6379/0'
CELERY_RESULT_BACKEND = 'redis://'+REDIS_URL+':6379/0'

# The cache settings
# For Iguana Redis is used
# see https://docs.djangoproject.com/en/1.11/ref/settings/#caches
CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": "redis://"+REDIS_URL+":6379/1",
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        }
    }
}


# E-Mail settings
# check for SendGrid backend
SENDGRID_API_KEY = get_setting(["email", "SENDGRID_API_KEY"], False, None)
if SENDGRID_API_KEY is None:
    # Use a SMTP mail server
    # see https://docs.djangoproject.com/en/1.11/ref/settings/#email-backend
    EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
    # see https://docs.djangoproject.com/en/1.11/ref/settings/#email-host
    EMAIL_HOST = get_setting(["email", "HOST"])
    # see https://docs.djangoproject.com/en/1.11/ref/settings/#email-port
    EMAIL_PORT = int(get_setting(["email", "PORT"]))
    # see https://docs.djangoproject.com/en/1.11/ref/settings/#email-host-user
    EMAIL_HOST_USER = get_setting(["email", "USER"])
    # see https://docs.djangoproject.com/en/1.11/ref/settings/#email-host-password
    EMAIL_HOST_PASSWORD = get_setting(["email", "PASSWORD"])
    # see https://docs.djangoproject.com/en/1.11/ref/settings/#email-use-tls
    EMAIL_USE_TLS = get_setting(["email", "USE_TLS"]) in ["true", "True"]
else:
    # use SendGrid
    EMAIL_BACKEND = "sgbackend.SendGridBackend"

# see https://docs.djangoproject.com/en/1.11/ref/settings/#std:setting-DEFAULT_FROM_EMAIL
DEFAULT_FROM_EMAIL = get_setting(["email", "FROM_EMAIL_ADDRESS"])
SERVER_EMAIL = get_setting(["email", "FROM_EMAIL_ADDRESS"])

EMAIL_RECIPIENT_IN_TO_HEADER = False


# Options for sendfile
# Iguana uses nginx as web server
SENDFILE_BACKEND = "sendfile.backends.nginx"
SENDFILE_ROOT = MEDIA_ROOT
# SENDFILE_URL must not end with a slash!
SENDFILE_URL = '/media'

# NOTE: Only needed when using nginx as web server!
# This allows django to access protected files by nginx.
# Here the 'media' directory is protected.
USE_X_ACCEL_REDIRECT = True
X_ACCEL_REDIRECT_PREFIX = "__media__"


# Slack integration
SLACK_ID = get_setting(["slack", "ID"], False)
SLACK_SECRET = get_setting(["slack", "SECRET"], False)
SLACK_VERIFICATION = get_setting(["slack", "VERIFICATION"], False)

# Olea-Bar - If set to true the previously assigned devs are replaced at the usage of @<dev0>[...@<devN>]
OLEA_REPLACE_DEVS = get_setting(["olea", "REPLACE_DEVS"], False, False)

REST_FRAMEWORK.update({
    'DEFAULT_RENDERER_CLASSES': (
        'rest_framework.renderers.JSONRenderer',
        ),
    'DEFAULT_PARSER_CLASSES': (
        'rest_framework.parsers.JSONParser',
        )
    })

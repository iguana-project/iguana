"""
This file contains all settings for running Iguana on a host.
"""

# First import the common settings
from .common import *
import json


# load the user settings JSON file
# the location is defined in the Ansible scripts
settings_file = open("/var/lib/iguana/settings/settings.json").read()
settings = json.loads(settings_file)


# function to get a setting from the settings.json
def get_setting(names, required=True, default=""):
    setting = settings[names[0]]
    for i in range(1, len(names)):
        setting = setting[names[i]]

    if required and not setting:
        raise Exception("A required setting is missing: " + " -> ".join(names))
    elif not setting:
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


# The settings for the database that should be used by django
# Iguana uses a Postgres SQL database
# see https://docs.djangoproject.com/en/1.11/ref/settings/#databases
DATABASES['default'] = {
        'ENGINE': "django.db.backends.postgresql_psycopg2",
        'NAME': get_setting(["database", "DATABASE_NAME"]),
        'USER': get_setting(["database", "USER"]),
        'PASSWORD': get_setting(["database", "PASSWORD"]),
        'HOST': get_setting(["database", "HOST"]),
        'PORT': get_setting(["database", "PORT"]),
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

REST_FRAMEWORK.update({
    'DEFAULT_RENDERER_CLASSES': (
        'rest_framework.renderers.JSONRenderer',
        ),
    'DEFAULT_PARSER_CLASSES': (
        'rest_framework.parsers.JSONParser',
        )
    })

from .common import *
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
"""
Settings for local developing.
"""

# enable debugging for developing
DEBUG = True


# enable admin interface for developing
ADMIN_ENABLED = True


HOST = 'localhost:8000'
# NOTE: ipv6 requests are rejected even it would be allowed here
ALLOWED_HOSTS = ['localhost', '127.0.0.1']


# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(FILES_DIR, 'db.sqlite3'),
        'TEST': {
            'NAME': os.path.join(FILES_DIR, 'test_db.sqlite3'),
        }
    }
}

# dummy cache
CACHES = {
    'default': {
            'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
     }
}

# this writes all emails to stdout, and does not actually send them via email
# NOTE: these settings are not suitable for production!!
# EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
EMAIL_BACKEND = 'django.core.mail.backends.filebased.EmailBackend'
EMAIL_FILE_PATH = EMAIL_DIR
EMAIL_RECIPIENT_IN_TO_HEADER = True

# NOTE: WARNING this is for testing-purpose only! This cause the captcha to accept "PASSED" as a valid input
CAPTCHA_TEST_MODE = 'True'
# NOTE: these settings are not suitable for production!! - END

# add the functional tests only for development
INSTALLED_APPS += [
    'test_without_migrations',
    'django_extensions',
    'functional_tests',
]


# Internationalization
LANGUAGE_CODE = "en-us"
USE_I18N = False
USE_L10N = False
TIME_ZONE = "UTC"
USE_TZ = True
CELERY_TIMEZONE = TIME_ZONE


SENDFILE_BACKEND = 'sendfile.backends.development'

# To make integration tests run
SLACK_SECRET = "foo"
SLACK_VERIFICATION = "bar"
SLACK_ID = "baz"

OLEA_REPLACE_DEVS = False

CELERY_BROKER_BACKEND = 'memory'
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True

# settings for functional tests
FUNCTESTS_DEFAULT_WAIT_TIMEOUT = 5
FUNCTESTS_HEADLESS_TESTING = True

# directory for files used for testing - This is the place where to put files used for testing but the recreation
# for each test run is too expensive
TEST_FILE_PATH = os.path.join(ROOT_DIR, "testing_files")

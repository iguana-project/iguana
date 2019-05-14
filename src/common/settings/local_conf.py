from .common import *
"""
Iguana (c) by Marc Ammon, Moritz Fickenscher, Lukas Fridolin,
Michael Gunselmann, Katrin Raab, Christian Strate

Iguana is licensed under a
Creative Commons Attribution-ShareAlike 4.0 International License.

You should have received a copy of the license along with this
work. If not, see <http://creativecommons.org/licenses/by-sa/4.0/>.
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

# directory for files used for testing - This is the place where to put files used for testing but the recreation
# for each test run is too expensive
TEST_FILE_PATH = os.path.join(ROOT_DIR, "testing_files")

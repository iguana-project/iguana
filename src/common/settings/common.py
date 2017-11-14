import os
import datetime
from django.contrib.messages import constants as messages

"""
Iguana (c) by Marc Ammon, Moritz Fickenscher, Lukas Fridolin,
Michael Gunselmann, Katrin Raab, Christian Strate

Iguana is licensed under a
Creative Commons Attribution-ShareAlike 4.0 International License.

You should have received a copy of the license along with this
work. If not, see <http://creativecommons.org/licenses/by-sa/4.0/>.
"""
"""
The common settings file.
"""


# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# Disable debugging by default
DEBUG = False


# Disable admin interface by default
ADMIN_ENABLED = False


# Application definition
INSTALLED_APPS = [
    'bootstrap3',
    'datetimewidget',
    'rest_framework',
    'refreshtoken',
    'django_filters',
    'pagedown',
    'cuser',
    'dal',
    'dal_select2',
    'event.apps.EventConfig',
    'gitintegration.apps.GitintegrationConfig',
    'api.apps.ApiConfig',
    'integration.apps.IntegrationConfig',
    'invite_users.apps.InviteUsersConfig',
    'issue.apps.IssueConfig',
    'kanbancol.apps.KanbanColConfig',
    'landing_page.apps.LandingPageConfig',
    'project.apps.ProjectConfig',
    'search.apps.SearchConfig',
    'sprint.apps.SprintConfig',
    'tag.apps.TagConfig',
    'timelog',
    'user_management',
    'user_profile.apps.UserProfileConfig',
    'captcha',  # django-simple-captcha
    'common',
    # NOTE: to get the activity stream plugim working under django 1.10 the following fix has to be applied:
    # NOTE: https://github.com/justquick/django-activity-stream/pull/311
    # NOTE: it has been fixed in master, but the latest release of the plugin is from summer last year
    'actstream',
    'discussion.apps.DiscussionConfig',
    # NOTE: it's important that django-pages are below our own ones, because otherwise django routes to their
    # NOTE: own auth-pages, and not through magic not to ours
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',
    'sendfile'
]


MIDDLEWARE = [
    'lib.csrf_update.csrfUpdateMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'cuser.middleware.CuserMiddleware',
    'lib.timezone_middleware.TimezoneMiddleware',
]


# the root file for the URL routing
ROOT_URLCONF = 'common.urls'


# where to find the templates
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]


WSGI_APPLICATION = 'common.wsgi.application'


# Database (should be set in the site specific settings)
DATABASES = {}


# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        # minimum of eight characters (default)
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
        'OPTIONS': {
            'user_attributes': ['username', 'first_name', 'last_name', 'email'],
            'max_similarity': 0.5,
        }
    },
    {
        # NOTE: you might wanna adjust the password list once again but please zip it after you did that
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
        'OPTIONS': {
            'password_list_path': os.path.realpath(os.path.join(BASE_DIR, "..", "..", "common_passwords",
                                                                "bigger_common_password_file.txt.gz"))
        }
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

AUTHENTICATION_BACKENDS = ['user_management.auth_backend.AuthBackend', ]


# Internationalization
LANGUAGE_CODE = 'en'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_L10N = True
USE_TZ = True


# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, "static")

# the directory were all media is stored
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
MEDIA_URL = '/media/'


# the directory where checked out repositories are stored
REPOSITORY_ROOT = os.path.join(MEDIA_ROOT, 'repos')


# Path to login page
LOGIN_URL = '/login/'


# Use the custom model-user-class instead of the default one
AUTH_USER_MODEL = 'user_management.CustomUser'


# change tag of error message to work with bootstrap 3
MESSAGE_TAGS = {
    messages.ERROR: 'danger'
}


# name of the platform
PLATFORM = "iguana-project"


# needed by activity stream plugin
SITE_ID = 1
# settings for the activity stream plugin
ACTSTREAM_SETTINGS = {
    'FETCH_RELATIONS': True,
    'USE_PREFETCH': True,
    'USE_JSONFIELD': False,
}


# for further captcha-settings see https://github.com/mbi/django-simple-captcha/blob/master/docs/advanced.rst
CAPTCHA_LENGTH = 6

REST_FRAMEWORK = {
        # added in global_conf so browsable API is activated in development
        # 'DEFAULT_RENDERER_CLASSES': (
        #           'rest_framework.renderers.JSONRenderer',
        #               )
        'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
        'PAGE_SIZE': 20,

        'DEFAULT_FILTER_BACKENDS': (
            'rest_framework_filters.backends.DjangoFilterBackend',
            ),

        'DEFAULT_AUTHENTICATION_CLASSES': (
            'rest_framework_jwt.authentication.JSONWebTokenAuthentication',
            'rest_framework.authentication.BasicAuthentication',
            ),
        'DEFAULT_PERMISSION_CLASSES': (
            'rest_framework.permissions.IsAuthenticated',
            )
        }

JWT_AUTH = {
    'JWT_EXPIRATION_DELTA': datetime.timedelta(minutes=5),
    'JWT_ALLOW_REFRESH': True,
    'JWT_REFRESH_EXPIRATION_DELTA': datetime.timedelta(days=28*6),
    'JWT_RESPONSE_PAYLOAD_HANDLER': 'lib.jwt_response_payload_handler.jwt_response_payload_handler',
    }


CELERY_BROKER_URL = 'redis://localhost:6379/0'
CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'

CELERY_TRACK_STARTED = True
CELERY_ENABLE_UTC = True
CELERY_TIMEZONE = 'Europe/London'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'

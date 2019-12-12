import os
import datetime
from django.contrib.messages import constants as messages
from django.core.validators import FileExtensionValidator

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


# The base path of the project (where the manage.py lies)
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))

# The root path of the project (one directory up)
ROOT_DIR = os.path.dirname(BASE_DIR)

# In this path files created by Iguana are stored
FILES_DIR = os.path.join(ROOT_DIR, "files")

# All emails send by Iguana are saved in this directory if no email server is provided
EMAIL_DIR = os.path.join(FILES_DIR, "emails")


# Disable debugging by default
DEBUG = False


# Disable admin interface by default
ADMIN_ENABLED = False


# Application definition
INSTALLED_APPS = [
    'bootstrap3',
    'bootstrap_datepicker_plus',
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
    'archive.apps.ArchiveConfig',
    'backlog.apps.BacklogConfig',
    'integration.apps.IntegrationConfig',
    'invite_users.apps.InviteUsersConfig',
    'issue.apps.IssueConfig',
    'kanbancol.apps.KanbanColConfig',
    'landing_page.apps.LandingPageConfig',
    'project.apps.ProjectConfig',
    'search.apps.SearchConfig',
    'sprint.apps.SprintConfig',
    'tag.apps.TagConfig',
    'timelog.apps.TimelogConfig',
    'olea.apps.OleaConfig',
    'user_management.apps.UserManagementConfig',
    'user_profile.apps.UserProfileConfig',
    'captcha',  # django-simple-captcha
    'common.apps.CommonConfig',
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
        'DIRS': [os.path.join(BASE_DIR, "common", "templates")],
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
            'password_list_path': os.path.join(ROOT_DIR, "common_passwords", "bigger_common_password_file.txt.gz"),
        }
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# used validator for image Uploads in CustomImageField
# NOTE: DO NOT add svg without a proper sanitize implementation for it in image_strip
#       svg is the only image type that is not recreated but the original file is stored
ALLOWED_IMG_EXTENSIONS = ['bmp', 'jpe', 'jpeg', 'jpg', 'gif', 'png']
ALLOWED_IMG_EXTENSION_VALIDATOR = [FileExtensionValidator(ALLOWED_IMG_EXTENSIONS)]
# The following ones have been removed because even though they can be stored successfully
# they won't get delivered successfully in all browser:        pbm, pgm, ppm, tif, tiff


# maximum file size for an image to be uploaded: 7 MiB
MAX_IMG_SIZE_BASE = 7
MAXIMUM_IMG_SIZE = MAX_IMG_SIZE_BASE*1024**2
# maximum file size for a file to be uploaded: 15 MiB
MAX_FILE_SIZE_BASE = 15
MAXIMUM_FILE_SIZE = MAX_FILE_SIZE_BASE*1024**2


AUTHENTICATION_BACKENDS = ['user_management.auth_backend.AuthBackend', ]


# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(ROOT_DIR, "static_files")

# the directory were all media is stored
MEDIA_ROOT = os.path.join(FILES_DIR, "media")
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
            'django_filters.rest_framework.DjangoFilterBackend',
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


# global celery settings
CELERY_TRACK_STARTED = True
CELERY_ENABLE_UTC = True
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'

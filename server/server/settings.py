"""
Django settings for server project.

For more information on this file, see
https://docs.djangoproject.com/en/dev/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/dev/ref/settings/
"""

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
import os
BASE_DIR = os.path.dirname(os.path.dirname(__file__))

# Hostname
import socket
try:
    HOSTNAME = socket.gethostname()
except:
    HOSTNAME = 'localhost'

import sys
TESTING = len(sys.argv) > 1 and sys.argv[1] == 'test'

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/dev/howto/deployment/checklist/


# Application definition

PROJECT_NAME = 'eins'

INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'import_export',
    'dash',
    'zemauth',
    'actionlog',
    'reports',
    'zweiapi',
    'convapi',
    'raven.contrib.django.raven_compat',
    'automation',
)

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware'
)

ROOT_URLCONF = 'server.urls'

WSGI_APPLICATION = 'server.wsgi.application'

# Internationalization
# https://docs.djangoproject.com/en/dev/topics/i18n/

LANGUAGE_CODE = 'en-us'

USE_TZ = False

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

TEMPLATE_CONTEXT_PROCESSORS = (
    'django.contrib.auth.context_processors.auth',
    'django.core.context_processors.request',
    'django.contrib.messages.context_processors.messages'
)
TEMPLATE_DIRS = (os.path.join(BASE_DIR, 'templates'),)

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/dev/howto/static-files/

STATICFILES_DIRS = (os.path.join(BASE_DIR, 'common_static'),)
STATIC_ROOT = 'static'

LOGIN_URL = '/signin'
LOGIN_REDIRECT_URL = '/'

AUTH_USER_MODEL = 'zemauth.User'

AUTHENTICATION_BACKENDS = (
    'zemauth.backends.EmailOrUsernameModelBackend',
)

TEST_RUNNER = 'utils.test_runner.CustomRunner'

TEST_OUTPUT_DIR = os.path.join(BASE_DIR, '.junit_xml')

COVERAGE_ENABLED = 'COVERAGE_ENABLED' in os.environ

DEFAULT_FROM_EMAIL = ''
MAILGUN_API_KEY = ''

DEMO_USERS = tuple()

from celeryconfig import *
from localsettings import *

STATIC_URL = SERVER_STATIC_URL + '/'

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format': '%(asctime)s [%(levelname)s] %(name)s PID=%(process)d: %(message)s'
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.handlers.WatchedFileHandler',
            'filename': LOG_FILE,
            'formatter': 'standard'
        },
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler'
        },
        'db_handler': {
            'level': 'INFO',
            'class': 'logging.handlers.WatchedFileHandler',
            'filename': LOG_FILE,
            'formatter': 'standard'
        },
        'sentry': {
            'level': 'WARNING',
            'class': 'raven.contrib.django.raven_compat.handlers.SentryHandler',
            'formatter': 'standard',
        },
    },
    'loggers': {
        'django.db.backends': {
            'handlers': ['db_handler'],
            'level': 'INFO',
            'propagate': False
        },
        'django.request': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
        },
        'newrelic.core.data_collector': {
            'level': 'ERROR',
        },
        'celery.worker': {
            'handlers': ['file', 'console'],
            'level': 'WARNING',
            'propagate': True
        },
        'requests.packages.urllib3': {
            'handlers': ['file', 'console'],
            'level': 'WARNING',
            'propagate': True
        },
        '': {
            'handlers': ['file', 'console', 'sentry'],
            'level': 'INFO',
        }
    }
}
CELERYD_LOG_FORMAT = LOGGING['formatters']['standard']['format']

if TESTING:
    LOGGING = None
    GOOGLE_OAUTH_ENABLED = False
    PAGER_DUTY_ENABLED = False
    USE_HASH_CACHE = False
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache'
        }
    }

    EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
    Z3_API_IMAGE_URL = ''
    Z3_API_THUMBNAIL_URL = ''

    CELERY_DEFAULT_CONVAPI_QUEUE = CELERY_DEFAULT_CONVAPI_QUEUE
    CELERY_DEFAULT_CONVAPI_V2_QUEUE = CELERY_DEFAULT_CONVAPI_V2_QUEUE

    if len(sys.argv) > 1 and '--redshift' not in sys.argv:
        # if not redshift testing
        DATABASES.pop(STATS_DB_NAME, None)
        DATABASES.pop(STATS_E2E_DB_NAME, None)
        STATS_DB_NAME = 'default'

# App specific
ACTIONLOG_RECENT_HOURS = 2

LAST_N_DAY_REPORTS = 3

SOURCE_OAUTH_URIS = {
    'yahoo': {
        'auth_uri': 'https://api.login.yahoo.com/oauth2/request_auth',
        'token_uri': 'https://api.login.yahoo.com/oauth2/get_token',
    }
}

PASSWORD_RESET_TIMEOUT_DAYS = 7

# Time zone used to convert datetimes in API responses
DEFAULT_TIME_ZONE = 'America/New_York'

# Placeholder value for source_campaign_key while campaign is being created
SOURCE_CAMPAIGN_KEY_PENDING_VALUE = 'PENDING'

CONVERSION_PIXEL_PREFIX = 'https://p1.zemanta.com/p/'

if os.environ.get('E2E'):
    print 'Using E2E database !!!'
    DATABASES['default'] = DATABASES['e2e']

if os.environ.get('E2E_REDDB'):
    DATABASES[STATS_DB_NAME]['NAME'] = os.environ.get('E2E_REDDB')
    print 'Using e2e Redshift DB named', DATABASES[STATS_DB_NAME]['NAME']

    if os.environ.get('REDSHIFT_E2E_USER'):
        credentials = {
            'USER': os.environ.get('REDSHIFT_E2E_USER'),
            'PASSWORD': os.environ.get('REDSHIFT_E2E_PASS'),
            'HOST': os.environ.get('REDSHIFT_E2E_HOST')
        }

        DATABASES[STATS_E2E_DB_NAME].update(credentials)
    else:
        credentials = {
            'USER': DATABASES[STATS_E2E_DB_NAME]['USER'],
            'PASSWORD': DATABASES[STATS_E2E_DB_NAME]['PASSWORD'],
            'HOST': DATABASES[STATS_E2E_DB_NAME]['HOST']
        }

    DATABASES[STATS_DB_NAME].update(credentials)


if 'e2e' in DATABASES:
    DATABASES['e2e'] = {}
    del DATABASES['e2e']


# User agent used when validating uploaded content ads URLs
URL_VALIDATOR_USER_AGENT = 'Mozilla/5.0 (compatible; Zemanta/1.0; +http://www.zemanta.com)'

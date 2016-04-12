"""
Django settings for server project.

For more information on this file, see
https://docs.djangoproject.com/en/dev/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/dev/ref/settings/
"""

from secretcrypt import Secret

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

PROJECT_NAME = 'z1'

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
    'k1api',
    'convapi',
    'raven.contrib.django.raven_compat',
    'automation',
    'timezone_field',
)

MIDDLEWARE_CLASSES = [
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'server.urls'

WSGI_APPLICATION = 'server.wsgi.application'

# Internationalization
# https://docs.djangoproject.com/en/dev/topics/i18n/

LANGUAGE_CODE = 'en-us'

USE_TZ = False

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            os.path.join(BASE_DIR, 'templates')
        ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.contrib.auth.context_processors.auth',
                'django.template.context_processors.request',
                'django.contrib.messages.context_processors.messages'
            ],
        },
    },
]

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

try:
    import qinspect
    MIDDLEWARE_CLASSES.append('qinspect.middleware.QueryInspectMiddleware'),
    # Query inspector settings, https://github.com/dobarkod/django-queryinspect
    # Whether the Query Inspector should do anything (default: False)
    QUERY_INSPECT_ENABLED = True
    # Whether to log the stats via Django logging (default: True)
    QUERY_INSPECT_LOG_STATS = True
    # Whether to log duplicate queries (default: False)
    QUERY_INSPECT_LOG_QUERIES = True
    # Whether to log queries that are above an absolute limit (default: None - disabled)
    QUERY_INSPECT_ABSOLUTE_LIMIT = 1000  # in milliseconds
    # Whether to include tracebacks in the logs (default: False)
    QUERY_INSPECT_LOG_TRACEBACKS = True
except ImportError:
    pass


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
        'qinspect': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': True,
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
    IMAGE_THUMBNAIL_URL = ''

    CELERY_DEFAULT_CONVAPI_QUEUE = CELERY_DEFAULT_CONVAPI_QUEUE
    CELERY_DEFAULT_CONVAPI_V2_QUEUE = CELERY_DEFAULT_CONVAPI_V2_QUEUE

    TESTING_DB_PREFIX = 'testing_'
    testing_databases = {db: DATABASES[db] for db in DATABASES.keys() if db.startswith(TESTING_DB_PREFIX)}
    for database_name in DATABASES.keys():
        if database_name.startswith(TESTING_DB_PREFIX):
            continue
        testing_db_replacement = 'testing_{}'.format(database_name)
        if testing_db_replacement in testing_databases:
            DATABASES[database_name] = testing_databases[testing_db_replacement]
            print('Using {testdbname} instead of {dbname} for testing...'.format(
                testdbname=testing_db_replacement,
                dbname=database_name
            ))

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

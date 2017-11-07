"""
Django settings for server project.

For more information on this file, see
https://docs.djangoproject.com/en/dev/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/dev/ref/settings/
"""

import copy
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

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'import_export',
    'dash',
    'restapi',
    'zemauth',
    'k1api',
    'raven.contrib.django.raven_compat',
    'automation',
    'stats',
    'redshiftapi',
    'etl',
    'backtosql',
    'timezone_field',
    'rest_framework',
    'oauth2_provider',
    'analytics',
    'prodops',
    'integrations.bizwire',
    'dev',
]

MIDDLEWARE = [
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.security.SecurityMiddleware',
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
            os.path.join(BASE_DIR, 'templates'),
            os.path.join(BASE_DIR, 'utils/templates'),
            os.path.join(BASE_DIR, 'analytics/templates'),
        ],
        'OPTIONS': {
            'context_processors': [
                'django.contrib.auth.context_processors.auth',
                'django.template.context_processors.request',
                'django.contrib.messages.context_processors.messages'
            ],
            'loaders': [
                ('django.template.loaders.cached.Loader', [
                    'django.template.loaders.filesystem.Loader',
                    'django.template.loaders.app_directories.Loader',
                ]),
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

TEST_RUNNER = 'utils.test_runner.SplitTestsRunner'
if os.environ.get('CI_TEST'):
    TEST_RUNNER = 'utils.test_runner.CustomRunner'

TEST_OUTPUT_DIR = os.path.join(BASE_DIR, '.junit_xml')

COVERAGE_ENABLED = 'COVERAGE_ENABLED' in os.environ

DEFAULT_FROM_EMAIL = ''

ENABLE_DJANGO_EXTENSIONS = False
ENABLE_DEBUG_TOOLBAR = False

# cache settings
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
    },
    'breakdowns_rs': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
    },
    'dash_db_cache': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
    },
    'audience_sample_size': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
    },
    'inventory_planning': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
    },
    'local_memory_cache': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unique-snowflake',
        'TIMEOUT': 60,  # 1 min
    },
}

DATABASE_ROUTERS = ['utils.db_for_reads.router.UseReadReplicaRouter']

try:
    import qinspect
    MIDDLEWARE.append('qinspect.middleware.QueryInspectMiddleware'),
    # Query inspector settings, https://github.com/dobarkod/django-queryinspect
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

# HTTPS
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

RESTAPI_REPORTS_BUCKET = 'z1-rest-reports'

GLOBAL_BLACKLIST_ID = 1

REST_FRAMEWORK = {
    'UNICODE_JSON': False,
    'EXCEPTION_HANDLER': 'restapi.exceptions.custom_exception_handler',
}

ALL_ACCOUNTS_USE_BCM_V2 = False
DISABLE_FACEBOOK = True
SLACK_LOG_ENABLE = True

from localsettings import *

if ENABLE_DJANGO_EXTENSIONS:
    INSTALLED_APPS.append('django_extensions')

if ENABLE_DEBUG_TOOLBAR:
    INSTALLED_APPS.extend([
        'debug_toolbar',
        'debug_panel',
        'template_profiler_panel',
    ])

    MIDDLEWARE = [
        'debug_panel.middleware.DebugPanelMiddleware',
    ] + MIDDLEWARE

    DEBUG_TOOLBAR_PANELS = [
        'debug_toolbar.panels.versions.VersionsPanel',
        'debug_toolbar.panels.timer.TimerPanel',
        'debug_toolbar.panels.settings.SettingsPanel',
        'debug_toolbar.panels.headers.HeadersPanel',
        'debug_toolbar.panels.request.RequestPanel',
        'debug_toolbar.panels.sql.SQLPanel',
        'debug_toolbar.panels.staticfiles.StaticFilesPanel',
        'debug_toolbar.panels.templates.TemplatesPanel',
        'debug_toolbar.panels.cache.CachePanel',
        'debug_toolbar.panels.signals.SignalsPanel',
        'debug_toolbar.panels.logging.LoggingPanel',
        'debug_toolbar.panels.redirects.RedirectsPanel',
        'debug_toolbar.panels.profiling.ProfilingPanel',
        'template_profiler_panel.panels.template.TemplateProfilerPanel',
    ]

    def show_debug_toolbar(request):
        return ENABLE_DEBUG_TOOLBAR and not TESTING

    DEBUG_TOOLBAR_CONFIG = {
        'SHOW_TOOLBAR_CALLBACK': show_debug_toolbar,
        'RESULTS_CACHE_SIZE': 10000000,
        'SHOW_COLLAPSED': True,
    }

    # django debug panel cache
    CACHES['debug-panel'] = {
        'BACKEND': 'django.core.cache.backends.filebased.FileBasedCache',
        'LOCATION': '/var/tmp/debug-panel-cache',
        'TIMEOUT': 86400,
        'OPTIONS': {
            'MAX_ENTRIES': 1000000
        }
    }

STATIC_URL = SERVER_STATIC_URL + '/'

CELERYD_HIJACK_ROOT_LOGGER = False
CELERY_REDIRECT_STDOUTS = False
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format': '%(asctime)s [%(levelname)s] %(name)s PID=%(process)d: %(message)s'
        },
        'timestamp': {
            'format': '%(asctime)s: %(message)s'
        },
    },
    'handlers': {
        'file': {
            'level': 'DEBUG',
            'class': 'logging.handlers.WatchedFileHandler',
            'filename': LOG_FILE,
            'formatter': 'standard'
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'timestamp'
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
        'sentry-error': {
            'level': 'ERROR',
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
        'newrelic.core.data_collector': {
            'level': 'ERROR',
        },
        'django': {
            'handlers': ['file', 'console', 'sentry-error'],
            'level': 'INFO',
            'propagate': False,
        },
        'celery': {
            'handlers': ['file', 'console', 'sentry-error'],
            'level': 'WARNING',
            'propagate': False,
        },
        'kombu': {
            'handlers': ['file', 'console', 'sentry-error'],
            'level': 'WARNING',
            'propagate': False,
        },
        'boto': {
            'handlers': ['file', 'console', 'sentry-error'],
            'level': 'WARNING',
            'propagate': False,
        },
        'requests': {
            'handlers': ['file', 'console', 'sentry-error'],
            'level': 'WARNING',
            'propagate': False,
        },
        'qinspect': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': False,
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
        },
        'breakdowns_rs': {
            'BACKEND': 'django.core.cache.backends.dummy.DummyCache'
        },
        'audience_sample_size': {
            'BACKEND': 'django.core.cache.backends.dummy.DummyCache'
        },
        'inventory_planning': {
            'BACKEND': 'django.core.cache.backends.dummy.DummyCache'
        },
        'dash_db_cache': {
            'BACKEND': 'django.core.cache.backends.dummy.DummyCache'
        },
        'bizwire_cache': {
            'BACKEND': 'django.core.cache.backends.dummy.DummyCache'
        },
        'local_memory_cache': {
            'BACKEND': 'django.core.cache.backends.dummy.DummyCache'
        }
    }

    PASSWORD_HASHERS = [
        'django.contrib.auth.hashers.MD5PasswordHasher',
    ]

    EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
    Z3_API_IMAGE_URL = ''
    IMAGE_THUMBNAIL_URL = ''

    TESTING_DB_PREFIX = 'testing_'
    for database_name in DATABASES.keys():
        if database_name.startswith(TESTING_DB_PREFIX):
            continue
        testing_db_replacement = 'testing_{}'.format(database_name)
        if testing_db_replacement in DATABASES:
            # make a copy to avoid issues when using --parallel
            DATABASES[database_name] = copy.copy(DATABASES[testing_db_replacement])
            print('Using {testdbname} instead of {dbname} for testing...'.format(
                testdbname=testing_db_replacement,
                dbname=database_name
            ))

    if len(sys.argv) > 1 and '--redshift' not in sys.argv:
        # if not redshift testing
        DATABASES.pop(STATS_DB_NAME, None)
        STATS_DB_NAME = 'default'

# App specific
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

CONVERSION_PIXEL_PREFIX = 'https://p1.zemanta.com/p/'

# User agent used when validating uploaded content ads URLs
URL_VALIDATOR_USER_AGENT = 'Mozilla/5.0 (compatible; Zemanta/1.0; +http://www.zemanta.com)'

OAUTH2_PROVIDER = {
    # this is the list of available scopes
    'SCOPES': {'read': 'Read scope', 'write': 'Write scope'}
}

CELERY_TASK_SERIALIZER = 'pickle'
CELERY_RESULT_SERIALIZER = 'pickle'
CELERY_ACCEPT_CONTENT = {'pickle'}

RESTAPI_REPORTS_URL = 'https://%s.s3.amazonaws.com' % RESTAPI_REPORTS_BUCKET

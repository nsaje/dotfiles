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
    'dash',
    #'django_extensions',  # optional for visualizing models and other perks
    'zemauth',
    'actionlog',
    'reports',
    'zweiapi',
    'raven.contrib.django.raven_compat',
)

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'gadjo.requestprovider.middleware.RequestProvider'  # providing request object in model signals
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


TEMPLATE_DIRS = (os.path.join(BASE_DIR, 'templates'),)

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/dev/howto/static-files/

STATICFILES_DIRS = (os.path.join(BASE_DIR, 'common_static'),)

STATIC_ROOT = 'static'

STATIC_URL = '/static/'
LOGIN_URL = '/signin'
LOGIN_REDIRECT_URL = '/'

AUTH_USER_MODEL = 'zemauth.User'

AUTHENTICATION_BACKENDS = (
    'zemauth.backends.EmailOrUsernameModelBackend',
)

TEST_RUNNER = 'utils.test_runner.CustomRunner'

COVERAGE_ENABLED = 'COVERAGE_ENABLED' in os.environ

DEFAULT_FROM_EMAIL = ''

from localsettings import *

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
            'level': 'DEBUG',
            'class': 'logging.handlers.WatchedFileHandler',
            'filename': LOG_FILE,
            'formatter': 'standard'
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler'
        },
        'db_handler': {
            'level': 'INFO',
            'class': 'logging.handlers.WatchedFileHandler',
            'filename': LOG_FILE,
            'formatter': 'standard'
        },
        'sentry': {
            'level': 'ERROR',
            'class': 'raven.contrib.django.raven_compat.handlers.SentryHandler',
            'formatter': 'standard',
        },
    },
    'loggers': {
        'django.db.backends': {
            'handlers': ['db_handler'],
            'level': 'DEBUG',
            'propagate': False
        },
        'django.request': {
            'handlers': ['file', 'console'],
            'level': 'DEBUG',
            'propagate': True
        },
        '': {
            'handlers': ['file', 'console', 'sentry'],
            'level': 'DEBUG',
            'propagate': True
        }
    }
}


# App specific
ACTIONLOG_RECENT_HOURS = 2

LAST_N_DAY_REPORTS = 3

SOURCE_OAUTH_URIS = {
    'yahoo': {
        'auth_uri': 'https://api.login.yahoo.com/oauth2/request_auth',
        'token_uri': 'https://api.login.yahoo.com/oauth2/get_token',
    }
}

TIMEZONE = 'America/New_York'

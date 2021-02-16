"""
Django settings for server project.

For more information on this file, see
https://docs.djangoproject.com/en/dev/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/dev/ref/settings/
"""
# isort:skip_file
import copy
from datetime import timedelta

import sentry_sdk
import swinfra.logging
import daiquiri
import sentry_sdk.integrations.django
from secretcrypt import Secret

from dcron import constants as dcron_constants

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
import os

BASE_DIR = os.path.dirname(os.path.dirname(__file__))

# Hostname
import socket

try:
    HOSTNAME = socket.gethostname()
except:
    HOSTNAME = "localhost"

import sys

TESTING = len(sys.argv) > 1 and sys.argv[1] == "test"

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/dev/howto/deployment/checklist/


# Application definition

PROJECT_NAME = "z1"

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "tagulous",
    "import_export",
    "dash",
    "restapi",
    "zemauth",
    "k1api",
    "automation",
    "stats",
    "redshiftapi",
    "realtimeapi",
    "etl",
    "backtosql",
    "timezone_field",
    "rest_framework",
    "oauth2_provider",
    "analytics",
    "prodops",
    "integrations.product_feeds",
    "dcron",
    "dev",
    "demo",
    "drf_yasg",
    "django_celery_results",
    "apt",
]

MIDDLEWARE = [
    "server.middleware.trace_id_middleware.trace_id_middleware",
    "server.middleware.influx_middleware.queries_to_influx",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "server.middleware.logging_middleware.zem_logging_middleware",
    "server.middleware.metrics_middleware.zem_metrics_middleware",
]

ROOT_URLCONF = "server.urls"

WSGI_APPLICATION = "server.wsgi.application"

# Internationalization
# https://docs.djangoproject.com/en/dev/topics/i18n/

LANGUAGE_CODE = "en-us"

USE_TZ = False

TIME_ZONE = "UTC"

USE_I18N = True

USE_L10N = True

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [
            os.path.join(BASE_DIR, "templates"),
            os.path.join(BASE_DIR, "utils/templates"),
            os.path.join(BASE_DIR, "analytics/templates"),
            os.path.join(BASE_DIR, "dash/templates"),
        ],
        "OPTIONS": {
            "context_processors": [
                "django.contrib.auth.context_processors.auth",
                "django.template.context_processors.request",
                "django.contrib.messages.context_processors.messages",
            ],
            "loaders": [
                (
                    "django.template.loaders.cached.Loader",
                    ["django.template.loaders.filesystem.Loader", "django.template.loaders.app_directories.Loader"],
                )
            ],
        },
    }
]

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/dev/howto/static-files/

STATICFILES_DIRS = (os.path.join(BASE_DIR, "common_static"),)
STATIC_ROOT = "static"

LOGIN_URL = "/signin"
LOGIN_REDIRECT_URL = "/"
ALLOWED_REDIRECT_HOSTS = ["ssp.zemanta.com"]

AUTH_USER_MODEL = "zemauth.User"

AUTHENTICATION_BACKENDS = ("zemauth.backends.EmailOrUsernameModelBackend",)

TEST_RUNNER = "utils.test_runner.SplitTestsRunner"
if os.environ.get("CI_TEST"):
    TEST_RUNNER = "utils.test_runner.CustomRunner"

TEST_OUTPUT_DIR = os.path.join(BASE_DIR, ".junit_xml")

COVERAGE_ENABLED = "COVERAGE_ENABLED" in os.environ

DEFAULT_FROM_EMAIL = ""

ENABLE_DJANGO_EXTENSIONS = False
ENABLE_DEBUG_TOOLBAR = False
ENABLE_SILK = False

# cache settings
CACHES = {
    "default": {"BACKEND": "django.core.cache.backends.dummy.DummyCache"},
    "breakdowns_rs": {"BACKEND": "django.core.cache.backends.dummy.DummyCache"},
    "redshift_background": {"BACKEND": "django.core.cache.backends.dummy.DummyCache"},
    "dash_db_cache": {"BACKEND": "django.core.cache.backends.dummy.DummyCache"},
    "audience_sample_size": {"BACKEND": "django.core.cache.backends.dummy.DummyCache"},
    "inventory_planning": {"BACKEND": "django.core.cache.backends.dummy.DummyCache"},
    "local_memory_cache": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "unique-snowflake",
        "TIMEOUT": 60,  # 1 min
    },
    "entity_permission_cache": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "entity_permission_cache",
        "TIMEOUT": None,  # don't expire, cache invalidated when data manually updated,
    },
    "cluster_level_cache": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "cluster_level_cache",
    },
}

DATABASE_ROUTERS = ["utils.db_router.routers.UseReadReplicaRouter"]

try:
    import qinspect

    MIDDLEWARE.append("qinspect.middleware.QueryInspectMiddleware"),
    # Query inspector settings, https://github.com/dobarkod/django-queryinspect
    # Whether to log the stats via Django logging (default: True)
    QUERY_INSPECT_LOG_STATS = True
    # Whether to log duplicate queries (default: False)
    QUERY_INSPECT_LOG_QUERIES = True
    # Whether to log queries that are above an absolute limit (default: None - disabled)
    QUERY_INSPECT_ABSOLUTE_LIMIT = 1000  # in milliseconds
    # Whether to include tracebacks in the logs (default: False)
    QUERY_INSPECT_LOG_TRACEBACKS = False
except ImportError:
    pass

# HTTPS
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

RESTAPI_REPORTS_BUCKET = "z1-rest-reports"

AD_LOOKUP_AD_GROUP_ID = 1
APT_ACCOUNT_ID = 7178
APT_SOURCE_IDS = (196, 197)

REST_FRAMEWORK = {
    "UNICODE_JSON": False,
    "EXCEPTION_HANDLER": "restapi.common.exceptions.custom_exception_handler",
    "DEFAULT_VERSIONING_CLASS": "rest_framework.versioning.NamespaceVersioning",
}

DISABLE_FACEBOOK = True
SLACK_LOG_ENABLE = True
DISABLE_CAMPAIGNSTOP_SIGNALS = False

METRICS_PUSH_GATEWAY = ""
METRICS_PUSH_PERIOD_SECONDS = 20

from .localsettings import *

if ENABLE_DJANGO_EXTENSIONS:
    INSTALLED_APPS.append("django_extensions")

if ENABLE_DEBUG_TOOLBAR:
    INSTALLED_APPS.extend(["debug_toolbar", "debug_panel", "template_profiler_panel"])

    MIDDLEWARE.append("debug_panel.middleware.DebugPanelMiddleware")

    DEBUG_TOOLBAR_PANELS = [
        "debug_toolbar.panels.versions.VersionsPanel",
        "debug_toolbar.panels.timer.TimerPanel",
        "debug_toolbar.panels.settings.SettingsPanel",
        "debug_toolbar.panels.headers.HeadersPanel",
        "debug_toolbar.panels.request.RequestPanel",
        "debug_toolbar.panels.sql.SQLPanel",
        "debug_toolbar.panels.staticfiles.StaticFilesPanel",
        "debug_toolbar.panels.templates.TemplatesPanel",
        "debug_toolbar.panels.cache.CachePanel",
        "debug_toolbar.panels.signals.SignalsPanel",
        "debug_toolbar.panels.logging.LoggingPanel",
        "debug_toolbar.panels.redirects.RedirectsPanel",
        "debug_toolbar.panels.profiling.ProfilingPanel",
        "template_profiler_panel.panels.template.TemplateProfilerPanel",
    ]

    def show_debug_toolbar(request):
        return ENABLE_DEBUG_TOOLBAR and not TESTING

    DEBUG_TOOLBAR_CONFIG = {
        "SHOW_TOOLBAR_CALLBACK": show_debug_toolbar,
        "RESULTS_CACHE_SIZE": 10000000,
        "SHOW_COLLAPSED": True,
    }

    # django debug panel cache
    CACHES["debug-panel"] = {
        "BACKEND": "django.core.cache.backends.filebased.FileBasedCache",
        "LOCATION": "/var/tmp/debug-panel-cache",
        "TIMEOUT": 86400,
        "OPTIONS": {"MAX_ENTRIES": 1000000},
    }

if os.environ.get("IS_COLLECTSTATIC"):
    # just so that the static is included
    INSTALLED_APPS.extend(["debug_toolbar", "debug_panel", "template_profiler_panel"])

if ENABLE_SILK and not TESTING:
    MIDDLEWARE = ["silk.middleware.SilkyMiddleware"] + MIDDLEWARE

    INSTALLED_APPS.extend(["silk"])

STATIC_URL = SERVER_STATIC_URL + "/"

CELERYD_HIJACK_ROOT_LOGGER = False
CELERY_REDIRECT_STDOUTS = False

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "json": {"()": swinfra.logging.OBJsonFormatter, "version_getter": lambda: BUILD_NUMBER},
        "readable": {"()": daiquiri.formatter.ColorExtrasFormatter, "fmt": daiquiri.formatter.DEFAULT_EXTRAS_FORMAT},
    },
    "filters": {"trace_id": {"()": "server.logging.trace_id_filter.TraceIdFilter"}},
    "handlers": {
        "console": {
            "level": "DEBUG",
            "class": "logging.StreamHandler",
            "filters": ["trace_id"],
            "formatter": LOGGING_FORMATTER,
        }
    },
    "loggers": {
        "newrelic.core.data_collector": {"handlers": ["console"], "level": "ERROR"},
        "django": {"handlers": ["console"], "level": "INFO", "propagate": False},
        "celery": {"handlers": ["console"], "level": "WARNING", "propagate": False},
        "kombu": {"handlers": ["console"], "level": "WARNING", "propagate": False},
        "boto": {"handlers": ["console"], "level": "WARNING", "propagate": False},
        "requests": {"handlers": ["console"], "level": "WARNING", "propagate": False},
        "qinspect": {"handlers": ["console"], "level": "DEBUG", "propagate": False},
        "": {"handlers": ["console"], "level": "INFO"},
    },
}


if TESTING:
    DISABLE_CAMPAIGNSTOP_SIGNALS = True
    LOGGING = None
    GOOGLE_OAUTH_ENABLED = False
    PAGER_DUTY_ENABLED = False
    USE_HASH_CACHE = False
    SLACK_LOG_ENABLE = False

    CACHES = {
        "default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"},
        "breakdowns_rs": {"BACKEND": "django.core.cache.backends.dummy.DummyCache"},
        "redshift_background": {"BACKEND": "django.core.cache.backends.dummy.DummyCache"},
        "audience_sample_size": {"BACKEND": "django.core.cache.backends.dummy.DummyCache"},
        "inventory_planning": {"BACKEND": "django.core.cache.backends.dummy.DummyCache"},
        "dash_db_cache": {"BACKEND": "django.core.cache.backends.dummy.DummyCache"},
        "local_memory_cache": {"BACKEND": "django.core.cache.backends.dummy.DummyCache"},
        "entity_permission_cache": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "LOCATION": "entity_permission_cache",
            "TIMEOUT": None,  # don't expire, cache invalidated when data manually updated,
        },
        "cluster_level_cache": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "LOCATION": "cluster_level_cache",
        },
    }

    PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]

    EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
    Z3_API_IMAGE_URL = ""
    IMAGE_THUMBNAIL_URL = ""

    if len(sys.argv) > 1 and "--redshift" not in sys.argv:
        stats_databases = [STATS_DB_HOT_CLUSTER] + STATS_DB_POSTGRES + STATS_DB_COLD_CLUSTERS
        for db in stats_databases:
            DATABASES.pop(db, None)
        STATS_DB_HOT_CLUSTER = "default"

# App specific
LAST_N_DAY_REPORTS = 3

SOURCE_OAUTH_URIS = {
    "yahoo": {
        "auth_uri": "https://api.login.yahoo.com/oauth2/request_auth",
        "token_uri": "https://api.login.yahoo.com/oauth2/get_token",
    }
}

PASSWORD_RESET_TIMEOUT_DAYS = 7

PASSWORD_MIN_LENGTH = 9

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        "OPTIONS": {"min_length": PASSWORD_MIN_LENGTH},
    },
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# Time zone used to convert datetimes in API responses
DEFAULT_TIME_ZONE = "America/New_York"

CONVERSION_PIXEL_PREFIX = "https://p1.zemanta.com/p/"

# User agent used when validating uploaded content ads URLs
URL_VALIDATOR_USER_AGENT = "Mozilla/5.0 (compatible; Zemanta/1.0; +http://www.zemanta.com)"

OAUTH2_PROVIDER = {
    # this is the list of available scopes
    "SCOPES": {"read": "Read scope", "write": "Write scope"}
}

CELERY_TASK_SERIALIZER = "pickle"
CELERY_RESULT_SERIALIZER = "pickle"
CELERY_ACCEPT_CONTENT = {"pickle"}

RESTAPI_REPORTS_URL = "https://%s.s3.amazonaws.com" % RESTAPI_REPORTS_BUCKET

DCRON = {
    "base_command": "/home/ubuntu/docker-manage-py.sh",
    # Do not trigger alerts if the next scheduled iteration is due to run in this time margin.
    "check_margin": timedelta(seconds=5),
    # Job severity overrides.
    "severities": {
        "run_autopilot": dcron_constants.Severity.HIGH,
        "run_autopilot_legacy": dcron_constants.Severity.HIGH,  # TODO: RTAP: LEGACY
        "campaignstop_main": dcron_constants.Severity.HIGH,
        "campaignstop_simple": dcron_constants.Severity.HIGH,
        "campaignstop_selection": dcron_constants.Severity.HIGH,
        "campaignstop_midnight_refresh": dcron_constants.Severity.HIGH,
        "campaignstop_midnight": dcron_constants.Severity.HIGH,
        "campaignstop_monitor": dcron_constants.Severity.HIGH,
        "create_demand_report": dcron_constants.Severity.HIGH,
        "handle_auto_save_batches": dcron_constants.Severity.HIGH,
        "monitor_dailystatement_holes": dcron_constants.Severity.HIGH,
        "refresh_partnerstats": dcron_constants.Severity.HIGH,
        "send_supply_report_emails": dcron_constants.Severity.HIGH,
        "sync_publisher_groups": dcron_constants.Severity.HIGH,
    },
    # Job ownersip overrides.
    "ownerships": {
        "publisher_classification": dcron_constants.Ownership.PRODOPS,
        "refresh_partnerstats": dcron_constants.Ownership.PRODOPS,
        "send_supply_report_emails": dcron_constants.Ownership.PRODOPS,
    },
    # How long to wait before warning alert if job execution is late.
    "default_warning_wait": 300,  # 5 min
    # Job warning wait overrides.
    "warning_waits": {
        "campaignstop_simple": 1500,  # 25 min
        "refresh_etl": 600,  # 10 min
        "cross_check": 1800,  # 30 min
    },
    # Maximum duration of a job before alerting.
    "default_max_duration": 3600,  # 1h
    # Job maximum duration overrides.
    "max_durations": {
        "campaignstop_main": 3600,  # 60 min
        "campaignstop_selection": 7200,  # 120 min
        "clean_up_postgres_stats": 7200,  # 2h
        "create_demand_report": 7200,  # 2 h
        "refresh_etl": 15000.0,  # 4 h 10 min
        "refresh_audience_sample_size_cache": 8100.0,  # 2h 15 min
        "cross_check": 7200,  # 2h
        "sync_publisher_groups": 7200,  # 2h
    },
    # If the same job is run within this interval, the second should exit before doing anything.
    "default_min_separation": 30,
    "min_separations": {},
    "log_viewer_link": "http://kibana-eslogs.outbrain.com:5601/app/kibana#/discover?_g=(refreshInterval:(pause:!t,value:0),time:(from:now-24h,mode:quick,to:now))&_a=(columns:!(message),filters:!(('$state':(store:appState),meta:(alias:!n,disabled:!f,index:'9dd4dcf0-faf7-11e9-b914-e5fa1366bcac',key:app,negate:!f,params:(query:{command_name},type:phrase),type:phrase,value:{command_name}),query:(match:(app:(query:{command_name},type:phrase))))),index:'9dd4dcf0-faf7-11e9-b914-e5fa1366bcac',interval:auto,query:(language:kuery,query:''),sort:!('@timestamp',desc))",
    "log_viewer_link_live": "http://kibana-eslogs.outbrain.com:5601/app/kibana#/discover?_g=(refreshInterval:(pause:!t,value:0),time:(from:now-1h,mode:quick,to:now))&_a=(columns:!(message),filters:!(('$state':(store:appState),meta:(alias:!n,disabled:!f,index:'9dd4dcf0-faf7-11e9-b914-e5fa1366bcac',key:app,negate:!f,params:(query:{command_name},type:phrase),type:phrase,value:{command_name}),query:(match:(app:(query:{command_name},type:phrase)))),('$state':(store:appState),meta:(alias:!n,disabled:!f,index:'9dd4dcf0-faf7-11e9-b914-e5fa1366bcac',key:host,negate:!f,params:(query:{host},type:phrase),type:phrase,value:{host}),query:(match:(host:(query:{host},type:phrase))))),index:'9dd4dcf0-faf7-11e9-b914-e5fa1366bcac',interval:auto,query:(language:kuery,query:''),sort:!('@timestamp',desc))",
}

sentry_sdk.init(dsn=SENTRY_CONFIG["dsn"], integrations=[sentry_sdk.integrations.django.DjangoIntegration()])

APT_TESTS_PATH = os.path.join(BASE_DIR, "apt/")

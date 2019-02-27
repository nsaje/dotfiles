#!/usr/bin/env python

"""
Run a test server used for REST API acceptance testing or E2E testing.

Creates a separate test database and loads tests fixtures. Then it runs a server
against that database.
"""
# isort:skip_file
import argparse
import os
import signal
import sys

import cdecimal

# Ensure any import of decimal gets cdecimal instead.
sys.modules["decimal"] = cdecimal  # noqa

import django
import django.db.backends.base.creation
from django.db import connection
from django.core.management import call_command


class FixturesSource(object):
    ACCEPTANCE = "acceptance"
    E2E = "e2e"


os.environ["DJANGO_SETTINGS_MODULE"] = "server.settings"

parser = argparse.ArgumentParser(description="Run a test server used for REST API acceptance testing or E2E testing.")
parser.add_argument("addrport", nargs="?", default="0.0.0.0:8123")
parser.add_argument("--keepdb", dest="keepdb", action="store_true")
parser.add_argument("--autoreload", dest="autoreload", action="store_true")
parser.add_argument("--fixtures", dest="fixtures", default=FixturesSource.ACCEPTANCE)
args = parser.parse_args()

# OVERRIDE SETTINGS
from django.conf import settings  # noqa

settings.ALLOWED_HOSTS = ["*"]

settings.K1_DEMO_MODE = True
settings.R1_DEMO_MODE = True
settings.LAMBDA_CONTENT_UPLOAD_FUNCTION_NAME = "mock"
settings.DISABLE_SIGNALS = True

BUILD_NUMBER = None
if os.environ.get("BUILD"):
    BUILD_NUMBER = os.environ.get("BUILD")
    branch = os.environ.get("BRANCH")
    if branch and branch != "master":
        BUILD_NUMBER = branch[:20] + BUILD_NUMBER
elif os.path.isfile("build_number.txt"):
    with open("build_number.txt", "r") as build_number:
        BUILD_NUMBER = build_number.read().strip()

_ROOT_STATIC_URL = "https://one-static.zemanta.com/build-{}".format(BUILD_NUMBER)
settings.SERVER_STATIC_URL = _ROOT_STATIC_URL + "/server"
settings.CLIENT_STATIC_URL = _ROOT_STATIC_URL + "/client"

print("Setting up django")
django.setup()

print("Creating a test database...")
db = connection.creation.create_test_db(autoclobber=True, keepdb=args.keepdb)
print("Using test database: %s" % db)

print("Overriding CAMPAIGN_AUTOPILOT_ENABLED_VALUE in campaign manager...")
from core.models.campaign import manager  # noqa

manager.CAMPAIGN_AUTOPILOT_ENABLED_VALUE = False


def sigterm_handler(signum, frame):
    print("Cleaning up the test database %s" % db)
    connection.creation.destroy_test_db(db, keepdb=args.keepdb)
    sys.exit(0)


signal.signal(signal.SIGTERM, sigterm_handler)
signal.signal(signal.SIGINT, sigterm_handler)

print("Loading fixtures")
if args.fixtures == FixturesSource.E2E:
    # TODO (e2e-tests): Create fixtures for e2e tests
    # call_command("loaddata", *["test_e2e"])
    pass
elif args.fixtures == FixturesSource.ACCEPTANCE:
    call_command("loaddata", *["test_acceptance", "test_geolocations"])

print("Applying migrations to stats database")
call_command("apply_postgres_stats_migrations")

print("Running the server on %s" % args.addrport)
call_command("runserver", addrport=args.addrport, use_reloader=args.autoreload, use_threading=False)

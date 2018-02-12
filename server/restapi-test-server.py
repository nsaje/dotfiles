#!/usr/bin/env python
"""
Run a test server for REST API acceptance testing.

Creates a separate acceptance_test_$NAME database and loads
acceptance tests fixtures. Then it runs a server against that database.
"""

import argparse
import os
import signal
import sys

import cdecimal
# Ensure any import of decimal gets cdecimal instead.
sys.modules['decimal'] = cdecimal  # noqa

import django
import django.db.backends.base.creation
from django.db import connection
from django.core.management import call_command

os.environ['DJANGO_SETTINGS_MODULE'] = 'server.settings'
django.db.backends.base.creation.TEST_DATABASE_PREFIX = 'acceptance_test_'

parser = argparse.ArgumentParser(
    description='Run a test server for acceptance testing the REST API.')
parser.add_argument('addrport', nargs='?', default='0.0.0.0:8123')
parser.add_argument('--keepdb', dest='keepdb', action='store_true')
parser.add_argument('--autoreload', dest='autoreload', action='store_true')
args = parser.parse_args()

# OVERRIDE SETTINGS
from django.conf import settings  # noqa
settings.K1_DEMO_MODE = True
settings.R1_DEMO_MODE = True
settings.LAMBDA_CONTENT_UPLOAD_FUNCTION_NAME = 'mock'
settings.DISABLE_SIGNALS = True

print("Setting up django")
django.setup()

print("Creating a test database...")
db = connection.creation.create_test_db(autoclobber=True, keepdb=args.keepdb)
print("Using test database: %s" % db)


def sigterm_handler(signum, frame):
    print("Cleaning up the test database %s" % db)
    connection.creation.destroy_test_db(db, keepdb=args.keepdb)
    sys.exit(0)


signal.signal(signal.SIGTERM, sigterm_handler)
signal.signal(signal.SIGINT, sigterm_handler)

print("Loading fixtures")
call_command('loaddata', *['test_acceptance', 'test_geolocations'])
print("Running the server on %s" % args.addrport)
call_command('runserver', addrport=args.addrport,
             use_reloader=args.autoreload, use_threading=False)

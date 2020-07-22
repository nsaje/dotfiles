#!/bin/bash

# Fail hard and fast
set -eo pipefail

CONF_ENV=apt python manage.py apt_test --emit-metrics && echo "PASSED" || echo "FAILED"
exit $?

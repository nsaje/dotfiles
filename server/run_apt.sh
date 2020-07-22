#!/bin/bash

# Fail hard and fast
set -eo pipefail

CONF_ENV=apt python manage.py apt_test --parallel=4 --emit-metrics && echo "PASSED" || echo "FAILED"
exit $?

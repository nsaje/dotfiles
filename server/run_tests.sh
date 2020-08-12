#!/bin/bash

# Fail hard and fast
set -eo pipefail

#coverage run manage.py test --failfast --noinput --parallel=4 --timing --keepdb && echo "PASSED" || echo "FAILED"
NO_CORES=$(grep -c ^processor /proc/cpuinfo)
python manage.py test --noinput --parallel=${NO_CORES} --timing && echo "PASSED" || echo "FAILED"
exit $?

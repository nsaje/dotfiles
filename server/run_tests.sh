#!/bin/bash

# Fail hard and fast
set -eo pipefail

#coverage run manage.py test --failfast --noinput --parallel=4 --timing --keepdb && echo "PASSED" || echo "FAILED"
python manage.py test --noinput --parallel=2 --timing && echo "PASSED" || echo "FAILED"
exit $?

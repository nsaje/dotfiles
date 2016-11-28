#!/bin/bash -x

# Fail hard and fast
set -eo pipefail

msg() {
        echo -e "[zemanta-z1] $@"
}

# Check if all requirements are installed
diff --brief requirements.txt /requirements.txt-installed || msg "requrements.txt differ. Update docker image."

exec $@

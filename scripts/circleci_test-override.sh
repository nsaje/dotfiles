#!/bin/bash

# Fail hard and fast
set -eo pipefail

case $CIRCLE_NODE_INDEX in
    0)
        # Setup test
        make login
        /usr/bin/time -f "1) real %e" make rebuild_if_differ
        /usr/bin/time -f "2) real %e" make build || true &
        /usr/bin/time -f "3) real %e" make run  &
        pip install pep8 xenon
        wait

        # Run test
        /usr/bin/time -f "4) real %e" /usr/local/bin/docker-compose run eins ./run_tests.sh | tee /dev/tty | tail -n 10 | grep "PASSED"
        ;;
    1)
        # Setup test
        for pkg in eslint eslint-plugin-jasmine bower grunt; do
            npm install -g $pkg &
        done
        wait
        cd client
        npm prune && npm install && bower install
        cd ..

        # Run test
        ./lint_check.sh && cd client && grunt prod --build-number ${CIRCLE_BUILD_NUM}
        ;;
esac

#!/usr/bin/env bash

set -o pipefail

TESTRARGS=$@

if [ ! -d .testrepository ]; then
    testr init
fi
testr run --subunit $TESTRARGS | subunit-trace -f -n
retval=$?
testr slowest

exit $retval

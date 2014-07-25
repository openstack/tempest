#!/usr/bin/env bash

set -o pipefail

TESTRARGS=$@

if [ ! -d .testrepository ]; then
    testr init
fi
testr run --subunit $TESTRARGS | $(dirname $0)/subunit-trace.py -f -n
retval=$?
testr slowest

exit $retval

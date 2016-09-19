#!/usr/bin/env bash

echo "WARNING: This script is deprecated and will be removed in the near future. Please migrate to tempest run or another method of launching a test runner"

set -o pipefail

TESTRARGS=$@

if [ ! -d .testrepository ]; then
    testr init
fi
testr run --subunit $TESTRARGS | subunit-trace -f -n
retval=$?
testr slowest

exit $retval

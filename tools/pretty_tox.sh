#!/usr/bin/env bash

echo "WARNING: This script is deprecated and will be removed in the near future. Please migrate to tempest run or another method of launching a test runner"

set -o pipefail

TESTRARGS=$1
python setup.py testr --testr-args="--subunit $TESTRARGS" | subunit-trace --no-failure-debug -f
retval=$?
# NOTE(mtreinish) The pipe above would eat the slowest display from pbr's testr
# wrapper so just manually print the slowest tests.
echo -e "\nSlowest Tests:\n"
testr slowest
exit $retval

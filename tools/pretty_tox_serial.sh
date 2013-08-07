#!/bin/sh

TESTRARGS=$@

if [ ! -d .testrepository ]; then
    testr init
fi
testr run --subunit $TESTRARGS | subunit2pyunit
testr slowest

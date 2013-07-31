#!/bin/sh

TESTRARGS=$@

if [ ! -d .testrepository ]; then
    testr init
fi
testr run --subunit $TESTRARGS | subunit-2to1 | tools/colorizer.py
testr slowest

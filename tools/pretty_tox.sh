#!/bin/sh

TESTRARGS=$1
python setup.py testr --slowest --testr-args="--subunit $TESTRARGS" | subunit2pyunit

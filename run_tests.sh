#!/bin/bash

function usage {
  echo "Usage: $0 [OPTION]..."
  echo "Run Tempest test suite"
  echo ""
  echo "  -s, --smoke              Only run smoke tests"
  echo "  -w, --whitebox           Only run whitebox tests"
  echo "  -p, --pep8               Just run pep8"
  echo "  -h, --help               Print this usage message"
  echo "  -d. --debug              Debug this script -- set -o xtrace"
  exit
}

function process_option {
  case "$1" in
    -h|--help) usage;;
    -d|--debug) set -o xtrace;;
    -p|--pep8) let just_pep8=1;;
    -s|--smoke) noseargs="$noseargs --attr=type=smoke";;
    -w|--whitebox) noseargs="$noseargs --attr=type=whitebox";;
    *) noseargs="$noseargs $1"
  esac
}

noseargs="tempest"
just_pep8=0

export NOSE_WITH_OPENSTACK=1
export NOSE_OPENSTACK_COLOR=1
export NOSE_OPENSTACK_RED=15.00
export NOSE_OPENSTACK_YELLOW=3.00
export NOSE_OPENSTACK_SHOW_ELAPSED=1
export NOSE_OPENSTACK_STDOUT=1

for arg in "$@"; do
  process_option $arg
done

function run_tests {
  $NOSETESTS
}

function run_pep8 {
  echo "Running pep8 ..."
  PEP8_EXCLUDE="kong,etc,include,tools"
  PEP8_OPTIONS="--exclude=$PEP8_EXCLUDE --repeat"
  PEP8_INCLUDE="."
  pep8 $PEP8_OPTIONS $PEP8_INCLUDE
}

NOSETESTS="nosetests $noseargs"

if [ $just_pep8 -eq 1 ]; then
    run_pep8
    exit
fi

run_tests || exit

if [ -z "$noseargs" ]; then
  run_pep8
fi

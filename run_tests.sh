#!/bin/bash

function usage {
  echo "Usage: [OPTIONS] [SUITES]"
  echo "Run all of the test suites"
  echo ""
  echo "  -h, --help               Print this usage message"
  echo ""
  echo "  The suites should be listed by the name of their directory."
  echo "  All other options are passed directly to the suites."
  exit
}

function process_option {
  case "$1" in
    -h|--help) usage;;
    -*|--*) test_opts="$test_opts $1";;
    *) tests="$tests $1"
  esac
}

for arg in "$@"; do
  process_option $arg
done

echo $test_opts

function run_tests {
  for test_dir in $tests
  do
    cd $test_dir
    test_cmd="./run_tests.sh ${test_opts}"
    echo "~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~"
    echo $test_cmd
    echo "~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~"
    $test_cmd
    cd ..
  done
}

run_tests || exit

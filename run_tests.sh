#!/usr/bin/env bash

function usage {
  echo "Usage: $0 [OPTION]..."
  echo "Run Tempest test suite"
  echo ""
  echo "  -V, --virtual-env        Always use virtualenv.  Install automatically if not present"
  echo "  -N, --no-virtual-env     Don't use virtualenv.  Run tests in local environment"
  echo "  -s, --no-site-packages   Isolate the virtualenv from the global Python environment"
  echo "  -f, --force              Force a clean re-build of the virtual environment. Useful when dependencies have been added."
  echo "  -s, --smoke              Only run smoke tests"
  echo "  -w, --whitebox           Only run whitebox tests"
  echo "  -c, --nova-coverage      Enable Nova coverage collection"
  echo "  -p, --pep8               Just run pep8"
  echo "  -h, --help               Print this usage message"
  echo "  -d, --debug              Debug this script -- set -o xtrace"
  echo "  -S, --stdout             Don't capture stdout"
  exit
}

function process_option {
  case "$1" in
    -h|--help) usage;;
    -V|--virtual-env) always_venv=1; never_venv=0;;
    -N|--no-virtual-env) always_venv=0; never_venv=1;;
    -s|--no-site-packages) no_site_packages=1;;
    -f|--force) force=1;;
    -d|--debug) set -o xtrace;;
    -c|--nova-coverage) let nova_coverage=1;;
    -p|--pep8) let just_pep8=1;;
    -s|--smoke) noseargs="$noseargs --attr=type=smoke";;
    -w|--whitebox) noseargs="$noseargs --attr=type=whitebox";;
    -S|--stdout) noseargs="$noseargs -s";;
    *) noseargs="$noseargs $1"
  esac
}

noseargs=""
just_pep8=0
venv=.venv
with_venv=tools/with_venv.sh
always_venv=0
never_venv=0
no_site_packages=0
force=0
wrapper=""
nova_coverage=0

export NOSE_WITH_OPENSTACK=1
export NOSE_OPENSTACK_COLOR=1
export NOSE_OPENSTACK_RED=15.00
export NOSE_OPENSTACK_YELLOW=3.00
export NOSE_OPENSTACK_SHOW_ELAPSED=1
export NOSE_OPENSTACK_STDOUT=1

for arg in "$@"; do
  process_option $arg
done

if [ $no_site_packages -eq 1 ]; then
  installvenvopts="--no-site-packages"
fi

# only add tempest default if we don't specify a test
if [[ "x$noseargs" =~ "tempest" ]]; then
  noseargs="$noseargs"
else
  noseargs="$noseargs tempest"
fi


function run_tests {
  ${wrapper} $NOSETESTS
}

function run_pep8 {
  echo "Running pep8 ..."
  srcfiles="`find tempest -type f -name "*.py"`"
  srcfiles+=" `find tools -type f -name "*.py"`"
  srcfiles+=" setup.py"

  ignore='--ignore=N4,E121,E122,E125,E126'

  ${wrapper} python tools/hacking.py ${ignore} ${srcfiles}
}

function run_coverage_start {
  echo "Starting nova-coverage"
  ${wrapper} python tools/tempest_coverage.py -c start
}

function run_coverage_report {
  echo "Generating nova-coverage report"
  ${wrapper} python tools/tempest_coverage.py -c report
}

NOSETESTS="nosetests $noseargs"

if [ $never_venv -eq 0 ]
then
  # Remove the virtual environment if --force used
  if [ $force -eq 1 ]; then
    echo "Cleaning virtualenv..."
    rm -rf ${venv}
  fi
  if [ -e ${venv} ]; then
    wrapper="${with_venv}"
  else
    if [ $always_venv -eq 1 ]; then
      # Automatically install the virtualenv
      python tools/install_venv.py $installvenvopts
      wrapper="${with_venv}"
    else
      echo -e "No virtual environment found...create one? (Y/n) \c"
      read use_ve
      if [ "x$use_ve" = "xY" -o "x$use_ve" = "x" -o "x$use_ve" = "xy" ]; then
        # Install the virtualenv and run the test suite in it
        python tools/install_venv.py $installvenvopts
        wrapper=${with_venv}
      fi
    fi
  fi
fi

if [ $just_pep8 -eq 1 ]; then
    run_pep8
    exit
fi

if [ $nova_coverage -eq 1 ]; then
    run_coverage_start
fi

run_tests

if [ $nova_coverage -eq 1 ]; then
    run_coverage_report
fi

if [ -z "$noseargs" ]; then
  run_pep8
fi

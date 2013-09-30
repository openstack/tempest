#!/usr/bin/env bash

function usage {
  echo "Usage: $0 [OPTION]..."
  echo "Run Tempest test suite"
  echo ""
  echo "  -V, --virtual-env        Always use virtualenv.  Install automatically if not present"
  echo "  -N, --no-virtual-env     Don't use virtualenv.  Run tests in local environment"
  echo "  -n, --no-site-packages   Isolate the virtualenv from the global Python environment"
  echo "  -f, --force              Force a clean re-build of the virtual environment. Useful when dependencies have been added."
  echo "  -u, --update             Update the virtual environment with any newer package versions"
  echo "  -s, --smoke              Only run smoke tests"
  echo "  -t, --serial             Run testr serially"
  echo "  -c, --nova-coverage      Enable Nova coverage collection"
  echo "  -C, --config             Config file location"
  echo "  -p, --pep8               Just run pep8"
  echo "  -h, --help               Print this usage message"
  echo "  -d, --debug              Debug this script -- set -o xtrace"
  echo "  -l, --logging            Enable logging"
  echo "  -L, --logging-config     Logging config file location.  Default is etc/logging.conf"
  echo "  -- [TESTROPTIONS]        After the first '--' you can pass arbitrary arguments to testr "
}

testrargs=""
just_pep8=0
venv=.venv
with_venv=tools/with_venv.sh
serial=0
always_venv=0
never_venv=0
no_site_packages=0
force=0
wrapper=""
nova_coverage=0
config_file=""
update=0
logging=0
logging_config=etc/logging.conf

if ! options=$(getopt -o VNnfustcphdC:lL: -l virtual-env,no-virtual-env,no-site-packages,force,update,smoke,serial,nova-coverage,pep8,help,debug,config:,logging,logging-config: -- "$@")
then
    # parse error
    usage
    exit 1
fi

eval set -- $options
first_uu=yes
while [ $# -gt 0 ]; do
  case "$1" in
    -h|--help) usage; exit;;
    -V|--virtual-env) always_venv=1; never_venv=0;;
    -N|--no-virtual-env) always_venv=0; never_venv=1;;
    -n|--no-site-packages) no_site_packages=1;;
    -f|--force) force=1;;
    -u|--update) update=1;;
    -d|--debug) set -o xtrace;;
    -c|--nova-coverage) let nova_coverage=1;;
    -C|--config) config_file=$2; shift;;
    -p|--pep8) let just_pep8=1;;
    -s|--smoke) testrargs+="smoke"; noseargs+="--attr=type=smoke";;
    -t|--serial) serial=1;;
    -l|--logging) logging=1;;
    -L|--logging-config) logging_config=$2; shift;;
    --) [ "yes" == "$first_uu" ] || testrargs="$testrargs $1"; first_uu=no  ;;
    *) testrargs="$testrargs $1"
  esac
  shift
done

if [ -n "$config_file" ]; then
    config_file=`readlink -f "$config_file"`
    export TEMPEST_CONFIG_DIR=`dirname "$config_file"`
    export TEMPEST_CONFIG=`basename "$config_file"`
fi

if [ $logging -eq 1 ]; then
    if [ ! -f "$logging_config" ]; then
        echo "No such logging config file: $logging_config"
        exit 1
    fi
    logging_config=`readlink -f "$logging_config"`
    export TEMPEST_LOG_CONFIG_DIR=`dirname "$logging_config"`
    export TEMPEST_LOG_CONFIG=`basename "$logging_config"`
fi

cd `dirname "$0"`

if [ $no_site_packages -eq 1 ]; then
  installvenvopts="--no-site-packages"
fi

function testr_init {
  if [ ! -d .testrepository ]; then
      ${wrapper} testr init
  fi
}

function run_tests {
  testr_init
  ${wrapper} find . -type f -name "*.pyc" -delete
  if [ $serial -eq 1 ]; then
      ${wrapper} testr run --subunit $testrargs | ${wrapper} subunit-2to1 | ${wrapper} tools/colorizer.py
  else
      ${wrapper} testr run --parallel --subunit $testrargs | ${wrapper} subunit-2to1 | ${wrapper} tools/colorizer.py
  fi
}

function run_tests_nose {
    NOSE_WITH_OPENSTACK=1
    NOSE_OPENSTACK_COLOR=1
    NOSE_OPENSTACK_RED=15.00
    NOSE_OPENSTACK_YELLOW=3.00
    NOSE_OPENSTACK_SHOW_ELAPSED=1
    NOSE_OPENSTACK_STDOUT=1
    if [[ "x$noseargs" =~ "tempest" ]]; then
        noseargs="$testrargs"
    else
        noseargs="$noseargs tempest"
    fi
    ${wrapper} nosetests $noseargs
}

function run_pep8 {
  echo "Running flake8 ..."
  if [ $never_venv -eq 1 ]; then
      echo "**WARNING**:" >&2
      echo "Running flake8 without virtual env may miss OpenStack HACKING detection" >&2
  fi
  ${wrapper} flake8
}

function run_coverage_start {
  echo "Starting nova-coverage"
  ${wrapper} python tools/tempest_coverage.py -c start
}

function run_coverage_report {
  echo "Generating nova-coverage report"
  ${wrapper} python tools/tempest_coverage.py -c report
}

if [ $never_venv -eq 0 ]
then
  # Remove the virtual environment if --force used
  if [ $force -eq 1 ]; then
    echo "Cleaning virtualenv..."
    rm -rf ${venv}
  fi
  if [ $update -eq 1 ]; then
      echo "Updating virtualenv..."
      python tools/install_venv.py $installvenvopts
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


py_version=`${wrapper} python --version 2>&1`
if [[ $py_version =~ "2.6" ]] ; then
    run_tests_nose
else
    run_tests
fi
retval=$?

if [ $nova_coverage -eq 1 ]; then
    run_coverage_report
fi

if [ -z "$testrargs" ]; then
    run_pep8
fi

exit $retval

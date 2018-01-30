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
  echo "  -C, --config             Config file location"
  echo "  -h, --help               Print this usage message"
  echo "  -d, --debug              Run tests with testtools instead of testr. This allows you to use PDB"
  echo "  -r, --result-xml         Path of Junitxml report to be generated"
  echo "  -p, --populate-config    Populate config file and init contrail environment"
  echo "  -- [TESTROPTIONS]        After the first '--' you can pass arbitrary arguments to testr"
}

testrargs=""
venv=${VENV:-.venv}
with_venv=tools/with_venv.sh
serial=0
always_venv=0
never_venv=0
no_site_packages=0
debug=0
force=0
coverage=0
wrapper=""
config_file=""
update=0
result_xml=result.xml
populate_config=0

if ! options=$(getopt -o VNnfusthdC:pr: -l virtual-env,no-virtual-env,no-site-packages,force,update,smoke,serial,help,debug,config:,populate-config,result-xml: -- "$@")
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
    -d|--debug) debug=1;;
    -C|--config) config_file=$2; shift;;
    -s|--suite) testrargs+=$2;;
    -p|--populate-config) populate_config=1;;
    -r|--result-xml) result_xml=$2; shift;;
    -t|--serial) serial=1;;
    --) [ "yes" == "$first_uu" ] || testrargs="$testrargs $1"; first_uu=no  ;;
    *) testrargs="$testrargs $1";;
  esac
  shift
done

if [ -n "$config_file" ]; then
    config_file=`readlink -f "$config_file"`
    export TEMPEST_CONFIG_DIR=`dirname "$config_file"`
    export TEMPEST_CONFIG=`basename "$config_file"`
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

function gen_report {
  last_entry=$(($(cat .testrepository/next-stream)-1))
  rm -f $result_xml
  ${wrapper} subunit-1to2 < .testrepository/$last_entry | subunit2junitxml -f -o $result_xml
}

function run_tests {
  testr_init
  ${wrapper} find . -type f -name "*.pyc" -delete
  export OS_TEST_PATH=./tempest/test_discover
  if [ $debug -eq 1 ]; then
      if [ "$testrargs" = "" ]; then
           testrargs="discover ./tempest/test_discover"
      fi
      ${wrapper} python -m testtools.run $testrargs
      return $?
  fi

  if [ $serial -eq 1 ]; then
      ${wrapper} testr run --subunit $testrargs
  else
      ${wrapper} testr run --parallel --subunit $testrargs
  fi
  gen_report
}

function apply_patches {
#  git apply contrail/bug_*.patch || exit 1
  git apply contrail/bug_1621622.patch || exit 1
}

echo "###### Ubuntu Main Repos
deb http://archive.ubuntu.com/ubuntu/ trusty main restricted universe
###### Ubuntu Update Repos
deb http://archive.ubuntu.com/ubuntu/ trusty-updates main restricted universe
" >& /etc/apt/sources.list.d/contrail-tempest.list

apt-get update
sudo apt-get install -y git sshpass gcc libxml2-dev libxslt-dev python-dev libffi-dev libssl-dev iputils-ping || exit 1
pip install virtualenv
rm /etc/apt/sources.list.d/contrail-tempest.list

if [ $never_venv -eq 0 ]
then
  # Remove the virtual environment if --force used
  if [ $force -eq 1 ]; then
    echo "Cleaning virtualenv..."
    rm -rf ${venv}
  fi
  if [ $update -eq 1 ]; then
      echo "Updating virtualenv..."
      virtualenv $installvenvopts $venv
      $venv/bin/pip install -U -r requirements.txt
  fi
  if [ -e ${venv} ]; then
    wrapper="${with_venv}"
  else
    if [ $always_venv -eq 1 ]; then
      # Automatically install the virtualenv
      virtualenv $installvenvopts $venv
      wrapper="${with_venv}"
      ${wrapper} pip install -U -r requirements.txt
    else
      echo -e "No virtual environment found...create one? (Y/n) \c"
      read use_ve
      if [ "x$use_ve" = "xY" -o "x$use_ve" = "x" -o "x$use_ve" = "xy" ]; then
        # Install the virtualenv and run the test suite in it
        virtualenv $installvenvopts $venv
        wrapper=${with_venv}
        ${wrapper} pip install -U -r requirements.txt
      fi
    fi
  fi
fi
if [ $populate_config -eq 1 ]; then
   (unset http_proxy && ./contrail/contrail-tempest-init.sh)
fi

apply_patches
(unset http_proxy && run_tests)
retval=$?

exit $retval

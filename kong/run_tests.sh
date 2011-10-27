#!/bin/bash

function usage {
  echo "Usage: $0 [OPTION]..."
  echo "Run the Kong test suite(s)"
  echo ""
  echo "  -V, --virtual-env        Always use virtualenv.  Install automatically if not present"
  echo "  -N, --no-virtual-env     Don't use virtualenv.  Run tests in local environment"
  echo "  -f, --force              Force a clean re-build of the virtual environment. Useful when dependencies have been added."
  echo "  -p, --pep8               Just run pep8"
  echo "  --nova		   Run all tests tagged as \"nova\"."
  echo "  --swift		   Run all tests tagged as \"swift\"."
  echo "  --glance		   Run all tests tagged as \"glance\"."
  echo "  -h, --help               Print this usage message"
  echo ""
  echo "Note: with no options specified, the script will try to run the tests in a virtual environment,"
  echo "      If no virtualenv is found, the script will ask if you would like to create one.  If you "
  echo "      prefer to run tests NOT in a virtual environment, simply pass the -N option."
  exit
}

function process_option {
  case "$1" in
    -h|--help) usage;;
    -V|--virtual-env) let always_venv=1; let never_venv=0;;
    -N|--no-virtual-env) let always_venv=0; let never_venv=1;;
    -f|--force) let force=1;;
    -p|--pep8) let just_pep8=1;;
    --nova) noseargs="$noseargs -a tags=nova";;
    --glance) noseargs="$noseargs -a tags=glance";;
    --swift) noseargs="$noseargs -a tags=swift";;
    *) noseargs="$noseargs $1"
  esac
}

base_dir=$(dirname $0)
venv=.kong-venv
with_venv=../tools/with_venv.sh
always_venv=0
never_venv=0
force=0
noseargs=
wrapper=""
just_pep8=0

for arg in "$@"; do
  process_option $arg
done

function run_tests {
  # Just run the test suites in current environment
  ${wrapper} $NOSETESTS 2> run_tests.err.log
}

function run_pep8 {
  echo "Running pep8 ..."
  PEP8_EXCLUDE=vcsversion.y
  PEP8_OPTIONS="--exclude=$PEP8_EXCLUDE --repeat --show-pep8 --show-source"
  PEP8_INCLUDE="tests tools run_tests.py"
  ${wrapper} pep8 $PEP8_OPTIONS $PEP8_INCLUDE || exit 1
}
NOSETESTS="env python run_tests.py $noseargs"
function setup_venv {
    if [ $never_venv -eq 0 ]
    then
        # Remove the virtual environment if --force used
        if [ $force -eq 1 ]; then
            echo "Cleaning virtualenv..."
            rm -rf ${venv}
        fi
        if [ -e "../${venv}" ]; then
            wrapper="${with_venv}"
        else
            if [ $always_venv -eq 1 ]; then
                # Automatically install the virtualenv
                use_ve='y'
            else
                echo -e "No virtual environment found...create one? (Y/n) \c"
                read use_ve
            fi
            if [ "x$use_ve" = "xY" -o "x$use_ve" = "x" -o "x$use_ve" = "xy" ]; then
                # Install the virtualenv and run the test suite in it
                env python ../tools/install_venv.py
                wrapper=${with_venv}
            fi
        fi
    fi
}

if [ $just_pep8 -eq 1 ]; then
    run_pep8
    exit
fi

cd $base_dir
setup_venv
run_tests || exit

#!/usr/bin/env bash

# Copyright 2017 Red Hat, Inc.
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

# This script is intended to check the sanity of tempest plugins against
# tempest master.
# What it does:
# * Retrieve the project lists having tempest plugin if project name is
#   given.
# * For each project in a list, it does:
#   * Create virtualenv and install tempest in it
#   * Clone the Project
#   * Install the Project and also installs dependencies from
#     test-requirements.txt.
#   * Create Tempest workspace
#   * List tempest plugins
#   * List tempest plugins tests
#   * Delete virtualenv and project repo
#
# If one of the step fails, The script will exit with failure.

if [ "$1" == "-h" ]; then
    echo -e "This script performs the sanity of tempest plugins to find
configuration and dependency issues with the tempest.\n
Usage: sh ./tools/tempest-plugin-sanity.sh [Run sanity on tempest plugins]"
    exit 0
fi

set -ex

# retrieve a list of projects having tempest plugins
PROJECT_LIST="$(python tools/generate-tempest-plugins-list.py)"

BLACKLIST="$(python tools/generate-tempest-plugins-list.py blacklist)"

# Function to clone project using zuul-cloner or from git
function clone_project {
    if [ -e /usr/zuul-env/bin/zuul-cloner ]; then
        /usr/zuul-env/bin/zuul-cloner --cache-dir /opt/git \
        https://opendev.org \
        "$1"

    elif [ -e /usr/bin/git ]; then
        /usr/bin/git clone https://opendev.org/"$1" \
        "$1"

    fi
}

# function to create virtualenv to perform sanity operation
function prepare_workspace {
    SANITY_DIR=$(pwd)
    virtualenv -p python3 --clear "$SANITY_DIR"/.venv
    export TVENV="$SANITY_DIR/tools/with_venv.sh"
    cd "$SANITY_DIR"

    # Install tempest with test dependencies in a venv
    "$TVENV" pip install -e . -r test-requirements.txt
}

# Function to install project
function install_project {
    "$TVENV" pip install "$SANITY_DIR"/"$1"
    # Check for test-requirements.txt file in a project then install it.
    if [ -e "$SANITY_DIR"/"$1"/test-requirements.txt ]; then
        "$TVENV" pip install -r "$SANITY_DIR"/"$1"/test-requirements.txt
    fi
}

# Function to perform sanity checking on Tempest plugin
function tempest_sanity {
    "$TVENV" tempest init "$SANITY_DIR"/tempest_sanity && \
    cd "$SANITY_DIR"/tempest_sanity && \
    "$TVENV" tempest list-plugins && \
    "$TVENV" tempest run -l
    retval=$?
    # Delete tempest workspace
    # NOTE: Cleaning should be done even if an error occurs.
    "$TVENV" tempest workspace remove --name tempest_sanity --rmdir
    cd "$SANITY_DIR"
    # Remove the sanity workspace in case of remaining
    rm -fr "$SANITY_DIR"/tempest_sanity
    # Remove the project directory after sanity run
    rm -fr "$SANITY_DIR"/"$1"

    return $retval
}

# Function to run sanity check on each project
function plugin_sanity_check {
    prepare_workspace && \
    clone_project "$1" && \
    install_project "$1" && \
    tempest_sanity "$1"

    return $?
}

# Log status
passed_plugin=''
failed_plugin=''
# Perform sanity on all tempest plugin projects
for project in $PROJECT_LIST; do
    # Remove blacklisted tempest plugins
    if ! [[ `echo $BLACKLIST | grep -c $project ` -gt 0 ]]; then
        plugin_sanity_check $project && passed_plugin+=", $project" || \
        failed_plugin+="$project, " > $SANITY_DIR/$project.txt
    fi
done

echo "Passed Plugins: $passed_plugin"
echo "Failed Plugins: $failed_plugin"

# Check for failed status
if [[ -n $failed_plugin ]]; then
    exit 1
fi

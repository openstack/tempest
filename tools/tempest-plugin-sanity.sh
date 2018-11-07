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
# * Creates the virtualenv
# * Install tempest
# * Retrieve the project lists having tempest plugin if project name is
#   given.
# * For each project in a list, It does:
#   * Clone the Project
#   * Install the Project and also installs dependencies from
#     test-requirements.txt.
#   * Create Tempest workspace
#   * List tempest plugins
#   * List tempest plugins tests
#   * Uninstall the project and its dependencies
#   * Again Install tempest
#   * Again repeat the step from cloning project
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
# List of projects having tempest plugin stale or unmaintained from long time
BLACKLIST="networking-plumgrid,trio2o"

# Function to clone project using zuul-cloner or from git
function clone_project() {
    if [ -e /usr/zuul-env/bin/zuul-cloner ]; then
        /usr/zuul-env/bin/zuul-cloner --cache-dir /opt/git \
        git://git.openstack.org \
        openstack/"$1"

    elif [ -e /usr/bin/git ]; then
        /usr/bin/git clone git://git.openstack.org/openstack/"$1" \
        openstack/"$1"

    fi
}

# Create virtualenv to perform sanity operation
SANITY_DIR=$(pwd)
virtualenv "$SANITY_DIR"/.venv
export TVENV="$SANITY_DIR/tools/with_venv.sh"
cd "$SANITY_DIR"

# Install tempest in a venv
"$TVENV" pip install .

# Function to install project
function install_project() {
    "$TVENV" pip install "$SANITY_DIR"/openstack/"$1"
    # Check for test-requirements.txt file in a project then install it.
    if [ -e "$SANITY_DIR"/openstack/"$1"/test-requirements.txt ]; then
        "$TVENV" pip install -r "$SANITY_DIR"/openstack/"$1"/test-requirements.txt
    fi
}

# Function to perform sanity checking on Tempest plugin
function tempest_sanity() {
    "$TVENV" tempest init "$SANITY_DIR"/tempest_sanity
    cd "$SANITY_DIR"/tempest_sanity
    "$TVENV" tempest list-plugins
    "$TVENV" tempest run -l
    # Delete tempest workspace
    "$TVENV" tempest workspace remove --name tempest_sanity --rmdir
    cd "$SANITY_DIR"
}

# Function to uninstall project
function uninstall_project() {
    "$TVENV" pip uninstall -y "$SANITY_DIR"/openstack/"$1"
    # Check for *requirements.txt file in a project then uninstall it.
    if [ -e "$SANITY_DIR"/openstack/"$1"/*requirements.txt ]; then
        "$TVENV" pip uninstall -y -r "$SANITY_DIR"/openstack/"$1"/*requirements.txt
    fi
    # Remove the project directory after sanity run
    rm -fr "$SANITY_DIR"/openstack/"$1"
}

# Function to run sanity check on each project
function plugin_sanity_check() {
    clone_project "$1"  &&  install_project "$1"  &&  tempest_sanity "$1" \
    &&  uninstall_project "$1"  &&  "$TVENV" pip install .
}

# Log status
passed_plugin=''
failed_plugin=''
# Perform sanity on all tempest plugin projects
for project in $PROJECT_LIST; do
    # Remove blacklisted tempest plugins
    if ! [[ `echo $BLACKLIST | grep -c $project ` -gt 0 ]]; then
        plugin_sanity_check $project && passed_plugin+=", $project" || \
        failed_plugin+=", $project"
    fi
done

# Check for failed status
if [[ -n $failed_plugin ]]; then
    exit 1
fi

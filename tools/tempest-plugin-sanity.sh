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
# List of projects having tempest plugin stale or unmaintained for a long time
# (6 months or more)
# TODO(masayukig): Some of these can be removed from BLACKLIST in the future.
# airship-tempest-plugin: https://review.openstack.org/#/c/634387/
# barbican-tempest-plugin: https://review.openstack.org/#/c/634631/
# intel-nfv-ci-tests: https://review.openstack.org/#/c/634640/
# networking-ansible: https://review.openstack.org/#/c/634647/
# networking-generic-switch: https://review.openstack.org/#/c/634846/
# networking-l2gw-tempest-plugin: https://review.openstack.org/#/c/635093/
# networking-midonet: https://review.openstack.org/#/c/635096/
# networking-plumgrid: https://review.openstack.org/#/c/635096/
# networking-spp: https://review.openstack.org/#/c/635098/
# neutron-dynamic-routing: https://review.openstack.org/#/c/637718/
# neutron-vpnaas: https://review.openstack.org/#/c/637719/
# nova-lxd: https://review.openstack.org/#/c/638334/
# valet: https://review.openstack.org/#/c/638339/
# vitrage-tempest-plugin: https://review.openstack.org/#/c/639003/
BLACKLIST="
airship-tempest-plugin
barbican-tempest-plugin
intel-nfv-ci-tests
networking-ansible
networking-generic-switch
networking-l2gw-tempest-plugin
networking-midonet
networking-plumgrid
networking-spp
neutron-dynamic-routing
neutron-vpnaas
nova-lxd
valet
vitrage-tempest-plugin
"

# Function to clone project using zuul-cloner or from git
function clone_project() {
    if [ -e /usr/zuul-env/bin/zuul-cloner ]; then
        /usr/zuul-env/bin/zuul-cloner --cache-dir /opt/git \
        https://git.openstack.org \
        openstack/"$1"

    elif [ -e /usr/bin/git ]; then
        /usr/bin/git clone https://git.openstack.org/openstack/"$1" \
        openstack/"$1"

    fi
}

# function to create virtualenv to perform sanity operation
function prepare_workspace() {
    SANITY_DIR=$(pwd)
    virtualenv --clear "$SANITY_DIR"/.venv
    export TVENV="$SANITY_DIR/tools/with_venv.sh"
    cd "$SANITY_DIR"

    # Install tempest with test dependencies in a venv
    "$TVENV" pip install -e . -r test-requirements.txt
}

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
    rm -fr "$SANITY_DIR"/openstack/"$1"

    return $retval
}

# Function to run sanity check on each project
function plugin_sanity_check() {
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

# Check for failed status
if [[ -n $failed_plugin ]]; then
    echo "Failed Plugins: $failed_plugin"
    exit 1
fi

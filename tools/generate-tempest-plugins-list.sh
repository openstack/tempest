#!/usr/bin/env bash

# Copyright 2016 Hewlett Packard Enterprise Development Company, L.P.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

# This script is intended to be run as a periodic proposal bot job
# in OpenStack infrastructure, though you can run it as a one-off.
#
# In order to function correctly, the environment in which the
# script runs must have
#   * a writable doc/source directory relative to the current
#     working directory
#   AND ( (
#   * git
#   * all git repos meant to be searched for plugins cloned and
#     at the desired level of up-to-datedness
#   * the environment variable git_dir pointing to the location
#   * of said git repositories
#   ) OR (
#   * network access to the review.openstack.org Gerrit API
#     working directory
#   * network access to https://git.openstack.org/cgit
#   ))
#
# If a file named doc/source/data/tempest-plugins-registry.header or
# doc/source/data/tempest-plugins-registry.footer is found relative to the
# current working directory, it will be prepended or appended to
# the generated reStructuredText plugins table respectively.

set -ex

(
declare -A plugins

if [[ -r doc/source/data/tempest-plugins-registry.header ]]; then
    cat doc/source/data/tempest-plugins-registry.header
fi

sorted_plugins=$(python tools/generate-tempest-plugins-list.py)

name_col_len=$(echo "${sorted_plugins}" | wc -L)
name_col_len=$(( name_col_len + 20 ))

# Print the title underline for a RST table.
function title_underline {
    printf "== "
    local len=$1
    while [[ $len -gt 0 ]]; do
        printf "="
        len=$(( len - 1))
    done
    printf " ===\n"
}

printf "\n\n"
title_underline ${name_col_len}
printf "%-3s %-${name_col_len}s %s\n" "SR" "Plugin Name" "URL"
title_underline ${name_col_len}

i=0
for plugin in ${sorted_plugins}; do
    i=$((i+1))
    giturl="git://git.openstack.org/openstack/${plugin}"
    gitlink="https://git.openstack.org/cgit/openstack/${plugin}"
    printf "%-3s %-${name_col_len}s %s\n" "$i" "${plugin}" "\`${giturl} <${gitlink}>\`__"
done

title_underline ${name_col_len}

printf "\n\n"

if [[ -r doc/source/data/tempest-plugins-registry.footer ]]; then
    cat doc/source/data/tempest-plugins-registry.footer
fi
) > doc/source/plugin-registry.rst

if [[ -n ${1} ]]; then
    cp doc/source/plugin-registry.rst ${1}/doc/source/plugin-registry.rst
fi

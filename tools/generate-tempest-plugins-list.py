#! /usr/bin/env python

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

# This script is intended to be run as part of a periodic proposal bot
# job in OpenStack infrastructure.
#
# In order to function correctly, the environment in which the
# script runs must have
#   * network access to the review.openstack.org Gerrit API
#     working directory
#   * network access to https://git.openstack.org/cgit

import json
import re

try:
    # For Python 3.0 and later
    from urllib.error import HTTPError
    import urllib.request as urllib
except ImportError:
    # Fall back to Python 2's urllib2
    import urllib2 as urllib
    from urllib2 import HTTPError


url = 'https://review.openstack.org/projects/'

# This is what a project looks like
'''
  "openstack-attic/akanda": {
    "id": "openstack-attic%2Fakanda",
    "state": "READ_ONLY"
  },
'''


def is_in_openstack_namespace(proj):
    return proj.startswith('openstack/')

# Rather than returning a 404 for a nonexistent file, cgit delivers a
# 0-byte response to a GET request.  It also does not provide a
# Content-Length in a HEAD response, so the way we tell if a file exists
# is to check the length of the entire GET response body.


def has_tempest_plugin(proj):
    try:
        r = urllib.urlopen(
            "https://git.openstack.org/cgit/%s/plain/setup.cfg" % proj)
    except HTTPError as err:
        if err.code == 404:
            return False
    p = re.compile(r'^tempest\.test_plugins', re.M)
    if p.findall(r.read().decode('utf-8')):
        return True
    else:
        False


r = urllib.urlopen(url)
# Gerrit prepends 4 garbage octets to the JSON, in order to counter
# cross-site scripting attacks.  Therefore we must discard it so the
# json library won't choke.
content = r.read().decode('utf-8')[4:]
projects = sorted(filter(is_in_openstack_namespace, json.loads(content)))

# Retrieve projects having no deb, puppet, ui or spec namespace as those
# namespaces do not contains tempest plugins.
projects_list = [i for i in projects if not (
    i.startswith('openstack/deb-') or
    i.startswith('openstack/puppet-') or
    i.endswith('-ui') or
    i.endswith('-specs'))]

found_plugins = list(filter(has_tempest_plugin, projects_list))

# Every element of the found_plugins list begins with "openstack/".
# We drop those initial 10 octets when printing the list.
for project in found_plugins:
    print(project[10:])

# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2013 IBM Corp.
#
#   Licensed under the Apache License, Version 2.0 (the "License"); you may
#   not use this file except in compliance with the License. You may obtain
#   a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#   WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#   License for the specific language governing permissions and limitations
#   under the License.

import re


PYTHON_CLIENTS = ['cinder', 'glance', 'keystone', 'nova', 'swift', 'quantum']

SKIP_DECORATOR_RE = re.compile(r'\s*@testtools.skip\((.*)\)')
SKIP_STR_RE = re.compile(r'.*Bug #\d+.*')
PYTHON_CLIENT_RE = re.compile('import (%s)client' % '|'.join(PYTHON_CLIENTS))


def skip_bugs(physical_line):
    """Check skip lines for proper bug entries

    T101: skips must contain "Bug #<bug_number>"
    """

    res = SKIP_DECORATOR_RE.match(physical_line)
    if res:
        content = res.group(1)
        res = SKIP_STR_RE.match(content)
        if not res:
            return (physical_line.find(content),
                    'T101: skips must contain "Bug #<bug_number>"')


def import_no_clients_in_api(physical_line, filename):
    """Check for client imports from tempest/api tests

    T102: Cannot import OpenStack python clients
    """

    if "tempest/api" in filename:
        res = PYTHON_CLIENT_RE.match(physical_line)
        if res:
            return (physical_line.find(res.group(1)),
                    ("T102: python clients import not allowed"
                     " in tempest/api/* tests"))


def import_no_files_in_tests(physical_line, filename):
    """Check for merges that try to land into tempest/tests

    T103: tempest/tests directory is deprecated
    """

    if "tempest/tests" in filename:
        return (0, ("T103: tempest/tests is deprecated"))


def factory(register):
    register(skip_bugs)
    register(import_no_clients_in_api)

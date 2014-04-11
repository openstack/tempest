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


PYTHON_CLIENTS = ['cinder', 'glance', 'keystone', 'nova', 'swift', 'neutron',
                  'trove', 'ironic', 'savanna', 'heat', 'ceilometer',
                  'marconi', 'sahara']

PYTHON_CLIENT_RE = re.compile('import (%s)client' % '|'.join(PYTHON_CLIENTS))
TEST_DEFINITION = re.compile(r'^\s*def test.*')
SETUPCLASS_DEFINITION = re.compile(r'^\s*def setUpClass')
SCENARIO_DECORATOR = re.compile(r'\s*@.*services\(')
VI_HEADER_RE = re.compile(r"^#\s+vim?:.+")


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


def scenario_tests_need_service_tags(physical_line, filename,
                                     previous_logical):
    """Check that scenario tests have service tags

    T104: Scenario tests require a services decorator
    """

    if 'tempest/scenario/test_' in filename:
        if TEST_DEFINITION.match(physical_line):
            if not SCENARIO_DECORATOR.match(previous_logical):
                return (physical_line.find('def'),
                        "T104: Scenario tests require a service decorator")


def no_setupclass_for_unit_tests(physical_line, filename):
    if 'tempest/tests' in filename:
        if SETUPCLASS_DEFINITION.match(physical_line):
            return (physical_line.find('def'),
                    "T105: setUpClass can not be used with unit tests")


def no_vi_headers(physical_line, line_number, lines):
    """Check for vi editor configuration in source files.

    By default vi modelines can only appear in the first or
    last 5 lines of a source file.

    T106
    """
    # NOTE(gilliard): line_number is 1-indexed
    if line_number <= 5 or line_number > len(lines) - 5:
        if VI_HEADER_RE.match(physical_line):
            return 0, "T106: Don't put vi configuration in source files"


def factory(register):
    register(import_no_clients_in_api)
    register(scenario_tests_need_service_tags)
    register(no_setupclass_for_unit_tests)
    register(no_vi_headers)

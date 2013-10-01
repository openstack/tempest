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


PYTHON_CLIENTS = ['cinder', 'glance', 'keystone', 'nova', 'swift', 'neutron']

PYTHON_CLIENT_RE = re.compile('import (%s)client' % '|'.join(PYTHON_CLIENTS))
TEST_DEFINITION = re.compile(r'^\s*def test.*')
SCENARIO_DECORATOR = re.compile(r'\s*@.*services\(')


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

    if 'tempest/scenario' in filename:
        if TEST_DEFINITION.match(physical_line):
            if not SCENARIO_DECORATOR.match(previous_logical):
                return (physical_line.find('def'),
                        "T104: Scenario tests require a service decorator")


def factory(register):
    register(import_no_clients_in_api)
    register(scenario_tests_need_service_tags)

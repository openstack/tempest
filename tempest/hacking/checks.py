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

import os
import re

import pep8


PYTHON_CLIENTS = ['cinder', 'glance', 'keystone', 'nova', 'swift', 'neutron',
                  'trove', 'ironic', 'savanna', 'heat', 'ceilometer',
                  'zaqar', 'sahara']

PYTHON_CLIENT_RE = re.compile('import (%s)client' % '|'.join(PYTHON_CLIENTS))
TEST_DEFINITION = re.compile(r'^\s*def test.*')
SETUP_TEARDOWN_CLASS_DEFINITION = re.compile(r'^\s+def (setUp|tearDown)Class')
SCENARIO_DECORATOR = re.compile(r'\s*@.*services\((.*)\)')
VI_HEADER_RE = re.compile(r"^#\s+vim?:.+")
mutable_default_args = re.compile(r"^\s*def .+\((.+=\{\}|.+=\[\])")


def import_no_clients_in_api_and_scenario_tests(physical_line, filename):
    """Check for client imports from tempest/api & tempest/scenario tests

    T102: Cannot import OpenStack python clients
    """

    if "tempest/api" in filename or "tempest/scenario" in filename:
        res = PYTHON_CLIENT_RE.match(physical_line)
        if res:
            return (physical_line.find(res.group(1)),
                    ("T102: python clients import not allowed"
                     " in tempest/api/* or tempest/scenario/* tests"))


def scenario_tests_need_service_tags(physical_line, filename,
                                     previous_logical):
    """Check that scenario tests have service tags

    T104: Scenario tests require a services decorator
    """

    if 'tempest/scenario/' in filename and '/test_' in filename:
        if TEST_DEFINITION.match(physical_line):
            if not SCENARIO_DECORATOR.match(previous_logical):
                return (physical_line.find('def'),
                        "T104: Scenario tests require a service decorator")


def no_setup_teardown_class_for_tests(physical_line, filename):

    if pep8.noqa(physical_line):
        return

    if 'tempest/test.py' not in filename:
        if SETUP_TEARDOWN_CLASS_DEFINITION.match(physical_line):
            return (physical_line.find('def'),
                    "T105: (setUp|tearDown)Class can not be used in tests")


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


def service_tags_not_in_module_path(physical_line, filename):
    """Check that a service tag isn't in the module path

    A service tag should only be added if the service name isn't already in
    the module path.

    T107
    """
    # NOTE(mtreinish) Scenario tests always need service tags, but subdirs are
    # created for services like heat which would cause false negatives for
    # those tests, so just exclude the scenario tests.
    if 'tempest/scenario' not in filename:
        matches = SCENARIO_DECORATOR.match(physical_line)
        if matches:
            services = matches.group(1).split(',')
            for service in services:
                service_name = service.strip().strip("'")
                modulepath = os.path.split(filename)[0]
                if service_name in modulepath:
                    return (physical_line.find(service_name),
                            "T107: service tag should not be in path")


def no_mutable_default_args(logical_line):
    """Check that mutable object isn't used as default argument

    N322: Method's default argument shouldn't be mutable
    """
    msg = "N322: Method's default argument shouldn't be mutable!"
    if mutable_default_args.match(logical_line):
        yield (0, msg)


def factory(register):
    register(import_no_clients_in_api_and_scenario_tests)
    register(scenario_tests_need_service_tags)
    register(no_setup_teardown_class_for_tests)
    register(no_vi_headers)
    register(service_tags_not_in_module_path)
    register(no_mutable_default_args)

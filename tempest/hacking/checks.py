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

from hacking import core
import pycodestyle


PYTHON_CLIENTS = ['cinder', 'glance', 'keystone', 'nova', 'swift', 'neutron',
                  'ironic', 'heat', 'sahara']

PYTHON_CLIENT_RE = re.compile('import (%s)client' % '|'.join(PYTHON_CLIENTS))
TEST_DEFINITION = re.compile(r'^\s*def test.*')
SETUP_TEARDOWN_CLASS_DEFINITION = re.compile(r'^\s+def (setUp|tearDown)Class')
SCENARIO_DECORATOR = re.compile(r'\s*@.*services\((.*)\)')
RAND_NAME_HYPHEN_RE = re.compile(r".*rand_name\(.+[\-\_][\"\']\)")
mutable_default_args = re.compile(r"^\s*def .+\((.+=\{\}|.+=\[\])")
TESTTOOLS_SKIP_DECORATOR = re.compile(r'\s*@testtools\.skip\((.*)\)')
METHOD = re.compile(r"^    def .+")
METHOD_GET_RESOURCE = re.compile(r"^\s*def (list|show)\_.+")
METHOD_DELETE_RESOURCE = re.compile(r"^\s*def delete_.+")
CLASS = re.compile(r"^class .+")
EX_ATTRIBUTE = re.compile(r'(\s+|\()(e|ex|exc|exception).message(\s+|\))')
NEGATIVE_TEST_DECORATOR = re.compile(
    r'\s*@decorators\.attr\(type=.*negative.*\)')
_HAVE_NEGATIVE_DECORATOR = False


@core.flake8ext
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


@core.flake8ext
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


@core.flake8ext
def no_setup_teardown_class_for_tests(physical_line, filename):

    if pycodestyle.noqa(physical_line):
        return

    if 'tempest/test.py' in filename or 'tempest/lib/' in filename:
        return

    if SETUP_TEARDOWN_CLASS_DEFINITION.match(physical_line):
        return (physical_line.find('def'),
                "T105: (setUp|tearDown)Class can not be used in tests")


@core.flake8ext
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


@core.flake8ext
def no_hyphen_at_end_of_rand_name(logical_line, filename):
    """Check no hyphen at the end of rand_name() argument

    T108
    """
    msg = "T108: hyphen should not be specified at the end of rand_name()"
    if RAND_NAME_HYPHEN_RE.match(logical_line):
        return 0, msg


@core.flake8ext
def no_mutable_default_args(logical_line):
    """Check that mutable object isn't used as default argument

    N322: Method's default argument shouldn't be mutable
    """
    msg = "N322: Method's default argument shouldn't be mutable!"
    if mutable_default_args.match(logical_line):
        yield (0, msg)


@core.flake8ext
def no_testtools_skip_decorator(logical_line):
    """Check that methods do not have the testtools.skip decorator

    T109
    """
    if TESTTOOLS_SKIP_DECORATOR.match(logical_line):
        yield (0, "T109: Cannot use testtools.skip decorator; instead use "
               "decorators.skip_because from tempest.lib")


def _common_service_clients_check(logical_line, physical_line, filename):
    if not re.match('tempest/(lib/)?services/.*', filename):
        return False

    if not METHOD.match(physical_line):
        return False

    if pycodestyle.noqa(physical_line):
        return False

    return True


@core.flake8ext
def get_resources_on_service_clients(physical_line, logical_line, filename,
                                     line_number, lines):
    """Check that service client names of GET should be consistent

    T110
    """
    if not _common_service_clients_check(logical_line, physical_line,
                                         filename):
        return

    for line in lines[line_number:]:
        if METHOD.match(line) or CLASS.match(line):
            # the end of a method
            return

        if 'self.get(' not in line and ('self.show_resource(' not in line and
                                        'self.list_resources(' not in line):
            continue

        if METHOD_GET_RESOURCE.match(logical_line):
            return

        msg = ("T110: [GET /resources] methods should be list_<resource name>s"
               " or show_<resource name>")
        yield (0, msg)


@core.flake8ext
def delete_resources_on_service_clients(physical_line, logical_line, filename,
                                        line_number, lines):
    """Check that service client names of DELETE should be consistent

    T111
    """
    if not _common_service_clients_check(logical_line, physical_line,
                                         filename):
        return

    for line in lines[line_number:]:
        if METHOD.match(line) or CLASS.match(line):
            # the end of a method
            return

        if 'self.delete(' not in line and 'self.delete_resource(' not in line:
            continue

        if METHOD_DELETE_RESOURCE.match(logical_line):
            return

        msg = ("T111: [DELETE /resources/<id>] methods should be "
               "delete_<resource name>")
        yield (0, msg)


@core.flake8ext
def dont_import_local_tempest_into_lib(logical_line, filename):
    """Check that tempest.lib should not import local tempest code

    T112
    """
    if 'tempest/lib/' not in filename:
        return

    if not ('from tempest' in logical_line or
            'import tempest' in logical_line):
        return

    if ('from tempest.lib' in logical_line or
            'import tempest.lib' in logical_line):
        return

    msg = ("T112: tempest.lib should not import local tempest code to avoid "
           "circular dependency")
    yield (0, msg)


@core.flake8ext
def use_rand_uuid_instead_of_uuid4(logical_line, filename):
    """Check that tests use data_utils.rand_uuid() instead of uuid.uuid4()

    T113
    """
    if 'tempest/lib/' in filename:
        return

    if 'uuid.uuid4()' not in logical_line:
        return

    msg = ("T113: Tests should use data_utils.rand_uuid()/rand_uuid_hex() "
           "instead of uuid.uuid4()/uuid.uuid4().hex")
    yield (0, msg)


@core.flake8ext
def dont_use_config_in_tempest_lib(logical_line, filename):
    """Check that tempest.lib doesn't use tempest config

    T114
    """

    if 'tempest/lib/' not in filename:
        return

    if ('tempest.config' in logical_line or
            'from tempest import config' in logical_line or
            'oslo_config' in logical_line):
        msg = ('T114: tempest.lib can not have any dependency on tempest '
               'config.')
        yield(0, msg)


@core.flake8ext
def dont_put_admin_tests_on_nonadmin_path(logical_line,
                                          filename):
    """Check admin tests should exist under admin path

    T115
    """

    if 'tempest/api/' not in filename:
        return

    if not re.match(r'class .*Test.*\(.*Admin.*\):', logical_line):
        return

    if not re.match(r'.\/tempest\/api\/.*\/admin\/.*', filename):
        msg = 'T115: All admin tests should exist under admin path.'
        yield(0, msg)


@core.flake8ext
def unsupported_exception_attribute_PY3(logical_line):
    """Check Unsupported 'message' exception attribute in PY3

    T116
    """
    result = EX_ATTRIBUTE.search(logical_line)
    msg = ("[T116] Unsupported 'message' Exception attribute in PY3")
    if result:
        yield(0, msg)


@core.flake8ext
def negative_test_attribute_always_applied_to_negative_tests(physical_line,
                                                             filename):
    """Check ``@decorators.attr(type=['negative'])`` applied to negative tests.

    T117
    """
    global _HAVE_NEGATIVE_DECORATOR

    if re.match(r'.\/tempest\/api\/.*_negative.*', filename):

        if NEGATIVE_TEST_DECORATOR.match(physical_line):
            _HAVE_NEGATIVE_DECORATOR = True
            return

        if TEST_DEFINITION.match(physical_line):
            if not _HAVE_NEGATIVE_DECORATOR:
                return (
                    0, "T117: Must apply `@decorators.attr(type=['negative'])`"
                       " to all negative API tests"
                )
            _HAVE_NEGATIVE_DECORATOR = False

#!/usr/bin/env python

# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2013 Quanta Research Cambridge, Inc.
#
#    Licensed under the Apache License, Version 2.0 (the "License");
#    you may not use this file except in compliance with the License.
#    You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS,
#    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    See the License for the specific language governing permissions and
#    limitations under the License.

import argparse
import json
import sys
from testtools.testsuite import iterate_tests
from unittest import loader


def discover_stress_tests(path="./", filter_attr=None):
    """Discovers all tempest tests and create action out of them
    """

    tests = []
    testloader = loader.TestLoader()
    list = testloader.discover(path)
    for func in (iterate_tests(list)):
        try:
            method_name = getattr(func, '_testMethodName')
            full_name = "%s.%s.%s" % (func.__module__,
                                      func.__class__.__name__,
                                      method_name)
            test_func = getattr(func, method_name)
            # NOTE(mkoderer): this contains a list of all type attributes
            attrs = getattr(test_func, "__testtools_attrs")
        except Exception:
            next
        if 'stress' in attrs:
            if filter_attr is not None and not filter_attr in attrs:
                continue
            class_setup_per = getattr(test_func, "st_class_setup_per")

            action = {'action':
                      "tempest.stress.actions.unit_test.UnitTest",
                      'kwargs': {"test_method": full_name,
                                 "class_setup_per": class_setup_per
                                 }
                      }
            tests.append(action)
    return tests


def main(ns):
    # NOTE(mkoderer): moved import to make "-h" possible without OpenStack
    from tempest.stress import driver
    result = 0
    if not ns.all:
        tests = json.load(open(ns.tests, 'r'))
    else:
        tests = discover_stress_tests(filter_attr=ns.type)

    if ns.serial:
        for test in tests:
            step_result = driver.stress_openstack([test],
                                                  ns.duration,
                                                  ns.number,
                                                  ns.stop)
            # NOTE(mkoderer): we just save the last result code
            if (step_result != 0):
                result = step_result
    else:
        driver.stress_openstack(tests, ns.duration, ns.number, ns.stop)
    return result


parser = argparse.ArgumentParser(description='Run stress tests. ')
parser.add_argument('-d', '--duration', default=300, type=int,
                    help="Duration of test in secs.")
parser.add_argument('-s', '--serial', action='store_true',
                    help="Trigger running tests serially.")
parser.add_argument('-S', '--stop', action='store_true',
                    default=False, help="Stop on first error.")
parser.add_argument('-n', '--number', type=int,
                    help="How often an action is executed for each process.")
group = parser.add_mutually_exclusive_group(required=True)
group.add_argument('-a', '--all', action='store_true',
                   help="Execute all stress tests")
parser.add_argument('-T', '--type',
                    help="Filters tests of a certain type (e.g. gate)")
group.add_argument('-t', "--tests", nargs='?',
                   help="Name of the file with test description.")

if __name__ == "__main__":
    sys.exit(main(parser.parse_args()))

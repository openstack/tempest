#!/usr/bin/env python

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
import inspect
import json
import sys
try:
    from unittest import loader
except ImportError:
    # unittest in python 2.6 does not contain loader, so uses unittest2
    from unittest2 import loader

from oslo_log import log as logging
from testtools import testsuite

from tempest.stress import driver

LOG = logging.getLogger(__name__)


def discover_stress_tests(path="./", filter_attr=None, call_inherited=False):
    """Discovers all tempest tests and create action out of them
    """
    LOG.info("Start test discovery")
    tests = []
    testloader = loader.TestLoader()
    list = testloader.discover(path)
    for func in (testsuite.iterate_tests(list)):
        attrs = []
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
            if filter_attr is not None and filter_attr not in attrs:
                continue
            class_setup_per = getattr(test_func, "st_class_setup_per")

            action = {'action':
                      "tempest.stress.actions.unit_test.UnitTest",
                      'kwargs': {"test_method": full_name,
                                 "class_setup_per": class_setup_per
                                 }
                      }
            if (not call_inherited and
                getattr(test_func, "st_allow_inheritance") is not True):
                class_structure = inspect.getmro(test_func.im_class)
                if test_func.__name__ not in class_structure[0].__dict__:
                    continue
            tests.append(action)
    return tests


parser = argparse.ArgumentParser(description='Run stress tests')
parser.add_argument('-d', '--duration', default=300, type=int,
                    help="Duration of test in secs")
parser.add_argument('-s', '--serial', action='store_true',
                    help="Trigger running tests serially")
parser.add_argument('-S', '--stop', action='store_true',
                    default=False, help="Stop on first error")
parser.add_argument('-n', '--number', type=int,
                    help="How often an action is executed for each process")
group = parser.add_mutually_exclusive_group(required=True)
group.add_argument('-a', '--all', action='store_true',
                   help="Execute all stress tests")
parser.add_argument('-T', '--type',
                    help="Filters tests of a certain type (e.g. gate)")
parser.add_argument('-i', '--call-inherited', action='store_true',
                    default=False,
                    help="Call also inherited function with stress attribute")
group.add_argument('-t', "--tests", nargs='?',
                   help="Name of the file with test description")


def main():
    ns = parser.parse_args()
    result = 0
    if not ns.all:
        tests = json.load(open(ns.tests, 'r'))
    else:
        tests = discover_stress_tests(filter_attr=ns.type,
                                      call_inherited=ns.call_inherited)

    if ns.serial:
        # Duration is total time
        duration = ns.duration / len(tests)
        for test in tests:
            step_result = driver.stress_openstack([test],
                                                  duration,
                                                  ns.number,
                                                  ns.stop)
            # NOTE(mkoderer): we just save the last result code
            if (step_result != 0):
                result = step_result
                if ns.stop:
                    return result
    else:
        result = driver.stress_openstack(tests,
                                         ns.duration,
                                         ns.number,
                                         ns.stop)
    return result


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        LOG.exception("Failure in the stress test framework")
        sys.exit(1)

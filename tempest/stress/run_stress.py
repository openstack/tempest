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


def main(ns):
    #NOTE(kodererm): moved import to make "-h" possible without OpenStack
    from tempest.stress import driver
    result = 0
    tests = json.load(open(ns.tests, 'r'))
    if ns.serial:
        for test in tests:
            step_result = driver.stress_openstack([test],
                                                  ns.duration,
                                                  ns.number)
            #NOTE(kodererm): we just save the last result code
            if (step_result != 0):
                result = step_result
    else:
        driver.stress_openstack(tests, ns.duration, ns.number)
    return result


parser = argparse.ArgumentParser(description='Run stress tests. ')
parser.add_argument('-d', '--duration', default=300, type=int,
                    help="Duration of test in secs.")
parser.add_argument('-s', '--serial', action='store_true',
                    help="Trigger running tests serially.")
parser.add_argument('-n', '--number', type=int,
                    help="How often an action is executed for each process.")
parser.add_argument('tests', help="Name of the file with test description.")

if __name__ == "__main__":
    sys.exit(main(parser.parse_args()))

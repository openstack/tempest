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

from tempest.stress import driver


def main(ns):
    tests = json.load(open(ns.tests, 'r'))
    driver.stress_openstack(tests, ns.duration)


parser = argparse.ArgumentParser(description='Run stress tests. ')
parser.add_argument('-d', '--duration', default=300, type=int,
                    help="Duration of test.")
parser.add_argument('tests', help="Name of the file with test description.")
main(parser.parse_args())

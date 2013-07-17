#!/usr/bin/env python
# vim: tabstop=4 shiftwidth=4 softtabstop=4
# Copyright 2013 IBM Corp.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import sys


def filter_classes(test_ids):
    test_classes = map(lambda x: x.rsplit('.', 1)[0], test_ids)

    #Remove duplicates from the list
    uniq_class = {}
    result = []
    for test_class in test_classes:
        if test_class in uniq_class:
            continue
        uniq_class[test_class] = 1
        result.append(test_class)
    return result


def usage():
    msg = """
    This command is used to filter out the unique list of test cases (classes)
    from a list of testr test_ids.

    Usage: run_test_classes.py <test id file>
          """
    print(msg)
    sys.exit(1)


def main():
    if len(sys.argv) == 2:
        test_list_path = sys.argv[1]
        test_list_file = open(test_list_path, 'r')
        test_list = test_list_file.readlines()
        for test_class in filter_classes(test_list):
            print test_class
        test_list_file.close()
    else:
        usage()

if __name__ == '__main__':
    main()

# Copyright 2014 Hewlett-Packard Development Company, L.P.
# All Rights Reserved.
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

from tempest.common import custom_matchers
from tempest.tests import base

from testtools.tests.matchers import helpers


class TestMatchesDictExceptForKeys(base.TestCase,
                                   helpers.TestMatchersInterface):

    matches_matcher = custom_matchers.MatchesDictExceptForKeys(
        {'a': 1, 'b': 2, 'c': 3, 'd': 4}, ['c', 'd'])
    matches_matches = [
        {'a': 1, 'b': 2, 'c': 3, 'd': 4},
        {'a': 1, 'b': 2, 'c': 5},
        {'a': 1, 'b': 2},
    ]
    matches_mismatches = [
        {},
        {'foo': 1},
        {'a': 1, 'b': 3},
        {'a': 1, 'b': 2, 'foo': 1},
        {'a': 1, 'b': None, 'foo': 1},
    ]

    str_examples = []
    describe_examples = [
        ("Only in expected:\n"
         "  {'a': 1, 'b': 2}\n",
         {},
         matches_matcher),
        ("Only in expected:\n"
         "  {'a': 1, 'b': 2}\n"
         "Only in actual:\n"
         "  {'foo': 1}\n",
         {'foo': 1},
         matches_matcher),
        ("Differences:\n"
         "  b: expected 2, actual 3\n",
         {'a': 1, 'b': 3},
         matches_matcher),
        ("Only in actual:\n"
         "  {'foo': 1}\n",
         {'a': 1, 'b': 2, 'foo': 1},
         matches_matcher),
        ("Only in actual:\n"
         "  {'foo': 1}\n"
         "Differences:\n"
         "  b: expected 2, actual None\n",
         {'a': 1, 'b': None, 'foo': 1},
         matches_matcher)
    ]

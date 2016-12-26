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


# Stolen from testtools/testtools/tests/matchers/helpers.py
class TestMatchersInterface(object):

    def test_matches_match(self):
        matcher = self.matches_matcher
        matches = self.matches_matches
        mismatches = self.matches_mismatches
        for candidate in matches:
            self.assertIsNone(matcher.match(candidate))
        for candidate in mismatches:
            mismatch = matcher.match(candidate)
            self.assertIsNotNone(mismatch)
            self.assertIsNotNone(getattr(mismatch, 'describe', None))

    def test__str__(self):
        # [(expected, object to __str__)].
        from testtools.matchers._doctest import DocTestMatches
        examples = self.str_examples
        for expected, matcher in examples:
            self.assertThat(matcher, DocTestMatches(expected))

    def test_describe_difference(self):
        # [(expected, matchee, matcher), ...]
        examples = self.describe_examples
        for difference, matchee, matcher in examples:
            mismatch = matcher.match(matchee)
            self.assertEqual(difference, mismatch.describe())

    def test_mismatch_details(self):
        # The mismatch object must provide get_details, which must return a
        # dictionary mapping names to Content objects.
        examples = self.describe_examples
        for difference, matchee, matcher in examples:
            mismatch = matcher.match(matchee)
            details = mismatch.get_details()
            self.assertEqual(dict(details), details)


class TestMatchesDictExceptForKeys(base.TestCase,
                                   TestMatchersInterface):

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

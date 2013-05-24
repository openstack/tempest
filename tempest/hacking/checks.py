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


SKIP_DECORATOR = '@testtools.skip('


def skip_bugs(physical_line):
    """Check skip lines for proper bug entries

    T101: Bug not in skip line
    T102: Bug in message formatted incorrectly
    """

    pos = physical_line.find(SKIP_DECORATOR)

    skip_re = re.compile(r'^\s*@testtools.skip.*')

    if pos != -1 and skip_re.match(physical_line):
        bug = re.compile(r'^.*\bbug\b.*', re.IGNORECASE)
        if bug.match(physical_line) is None:
            return (pos, 'T101: skips must have an associated bug')

        bug_re = re.compile(r'.*skip\(.*Bug\s\#\d+', re.IGNORECASE)

        if bug_re.match(physical_line) is None:
            return (pos, 'T102: Bug number formatted incorrectly')


def factory(register):
    register(skip_bugs)

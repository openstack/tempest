#!/usr/bin/env python
# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2012 OpenStack, LLC
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

"""
Track test skips via launchpadlib API and raise alerts if a bug
is fixed but a skip is still in the Tempest test code
"""

import logging
import os
import re

from launchpadlib import launchpad

BASEDIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
TESTDIR = os.path.join(BASEDIR, 'tempest', 'tests')
LPCACHEDIR = os.path.expanduser('~/.launchpadlib/cache')


def info(msg, *args, **kwargs):
    logging.info(msg, *args, **kwargs)


def debug(msg, *args, **kwargs):
    logging.debug(msg, *args, **kwargs)


def find_skips(start=TESTDIR):
    """
    Returns a list of tuples (method, bug) that represent
    test methods that have been decorated to skip because of
    a particular bug.
    """
    results = []
    debug("Searching in %s", start)
    for root, _dirs, files in os.walk(start):
        for name in files:
            if name.startswith('test_') and name.endswith('py'):
                path = os.path.join(root, name)
                debug("Searching in %s", path)
                results += find_skips_in_file(path)
    return results


def find_skips_in_file(path):
    """
    Return the skip tuples in a test file
    """
    BUG_RE = re.compile(r'.*skip\(.*[bB]ug\s*(\d+)')
    DEF_RE = re.compile(r'.*def (\w+)\(')
    bug_found = False
    results = []
    lines = open(path, 'rb').readlines()
    for x, line in enumerate(lines):
        if not bug_found:
            res = BUG_RE.match(line)
            if res:
                bug_no = int(res.group(1))
                debug("Found bug skip %s on line %d", bug_no, x + 1)
                bug_found = True
        else:
            res = DEF_RE.match(line)
            if res:
                method = res.group(1)
                debug("Found test method %s skips for bug %d", method, bug_no)
                results.append((method, bug_no))
                bug_found = False
    return results


if __name__ == '__main__':
    logging.basicConfig(format='%(levelname)s: %(message)s',
                        level=logging.INFO)
    results = find_skips()
    unique_bugs = sorted(set([bug for (method, bug) in results]))
    unskips = []
    duplicates = []
    info("Total bug skips found: %d", len(results))
    info("Total unique bugs causing skips: %d", len(unique_bugs))
    lp = launchpad.Launchpad.login_anonymously('grabbing bugs',
                                               'production',
                                               LPCACHEDIR)
    for bug_no in unique_bugs:
        bug = lp.bugs[bug_no]
        duplicate = bug.duplicate_of_link
        if duplicate is not None:
            dup_id = duplicate.split('/')[-1]
            duplicates.append((bug_no, dup_id))
        for task in bug.bug_tasks:
            info("Bug #%7s (%12s - %12s)", bug_no,
                 task.importance, task.status)
            if task.status in ('Fix Released', 'Fix Committed'):
                unskips.append(bug_no)

    for bug_id, dup_id in duplicates:
        if bug_id not in unskips:
            dup_bug = lp.bugs[dup_id]
            for task in dup_bug.bug_tasks:
                info("Bug #%7s is a duplicate of Bug#%7s (%12s - %12s)",
                     bug_id, dup_id, task.importance, task.status)
                if task.status in ('Fix Released', 'Fix Committed'):
                    unskips.append(bug_id)

    unskips = sorted(set(unskips))
    if unskips:
        print "The following bugs have been fixed and the corresponding skips"
        print "should be removed from the test cases:"
        print
        for bug in unskips:
            print "  %7s" % bug

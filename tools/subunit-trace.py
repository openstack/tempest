#!/usr/bin/env python

# Copyright 2014 Hewlett-Packard Development Company, L.P.
# Copyright 2014 Samsung Electronics
# All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

"""Trace a subunit stream in reasonable detail and high accuracy."""

import argparse
import functools
import re
import sys

import subunit
import testtools

DAY_SECONDS = 60 * 60 * 24
FAILS = []
RESULTS = {}


def cleanup_test_name(name, strip_tags=True, strip_scenarios=False):
    """Clean up the test name for display.

    By default we strip out the tags in the test because they don't help us
    in identifying the test that is run to it's result.

    Make it possible to strip out the testscenarios information (not to
    be confused with tempest scenarios) however that's often needed to
    indentify generated negative tests.
    """
    if strip_tags:
        tags_start = name.find('[')
        tags_end = name.find(']')
        if tags_start > 0 and tags_end > tags_start:
            newname = name[:tags_start]
            newname += name[tags_end + 1:]
            name = newname

    if strip_scenarios:
        tags_start = name.find('(')
        tags_end = name.find(')')
        if tags_start > 0 and tags_end > tags_start:
            newname = name[:tags_start]
            newname += name[tags_end + 1:]
            name = newname

    return name


def get_duration(timestamps):
    start, end = timestamps
    if not start or not end:
        duration = ''
    else:
        delta = end - start
        duration = '%d.%06ds' % (
            delta.days * DAY_SECONDS + delta.seconds, delta.microseconds)
    return duration


def find_worker(test):
    for tag in test['tags']:
        if tag.startswith('worker-'):
            return int(tag[7:])
    return 'NaN'


# Print out stdout/stderr if it exists, always
def print_attachments(stream, test, all_channels=False):
    """Print out subunit attachments.

    Print out subunit attachments that contain content. This
    runs in 2 modes, one for successes where we print out just stdout
    and stderr, and an override that dumps all the attachments.
    """
    channels = ('stdout', 'stderr')
    for name, detail in test['details'].items():
        # NOTE(sdague): the subunit names are a little crazy, and actually
        # are in the form pythonlogging:'' (with the colon and quotes)
        name = name.split(':')[0]
        if detail.content_type.type == 'test':
            detail.content_type.type = 'text'
        if (all_channels or name in channels) and detail.as_text():
            title = "Captured %s:" % name
            stream.write("\n%s\n%s\n" % (title, ('~' * len(title))))
            # indent attachment lines 4 spaces to make them visually
            # offset
            for line in detail.as_text().split('\n'):
                stream.write("    %s\n" % line)


def show_outcome(stream, test, print_failures=False):
    global RESULTS
    status = test['status']
    # TODO(sdague): ask lifeless why on this?
    if status == 'exists':
        return

    worker = find_worker(test)
    name = cleanup_test_name(test['id'])
    duration = get_duration(test['timestamps'])

    if worker not in RESULTS:
        RESULTS[worker] = []
    RESULTS[worker].append(test)

    # don't count the end of the return code as a fail
    if name == 'process-returncode':
        return

    if status == 'success':
        stream.write('{%s} %s [%s] ... ok\n' % (
            worker, name, duration))
        print_attachments(stream, test)
    elif status == 'fail':
        FAILS.append(test)
        stream.write('{%s} %s [%s] ... FAILED\n' % (
            worker, name, duration))
        if not print_failures:
            print_attachments(stream, test, all_channels=True)
    elif status == 'skip':
        stream.write('{%s} %s ... SKIPPED: %s\n' % (
            worker, name, test['details']['reason'].as_text()))
    else:
        stream.write('{%s} %s [%s] ... %s\n' % (
            worker, name, duration, test['status']))
        if not print_failures:
            print_attachments(stream, test, all_channels=True)

    stream.flush()


def print_fails(stream):
    """Print summary failure report.

    Currently unused, however there remains debate on inline vs. at end
    reporting, so leave the utility function for later use.
    """
    if not FAILS:
        return
    stream.write("\n==============================\n")
    stream.write("Failed %s tests - output below:" % len(FAILS))
    stream.write("\n==============================\n")
    for f in FAILS:
        stream.write("\n%s\n" % f['id'])
        stream.write("%s\n" % ('-' * len(f['id'])))
        print_attachments(stream, f, all_channels=True)
    stream.write('\n')


def count_tests(key, value):
    count = 0
    for k, v in RESULTS.items():
        for item in v:
            if key in item:
                if re.search(value, item[key]):
                    count += 1
    return count


def run_time():
    runtime = 0.0
    for k, v in RESULTS.items():
        for test in v:
            runtime += float(get_duration(test['timestamps']).strip('s'))
    return runtime


def worker_stats(worker):
    tests = RESULTS[worker]
    num_tests = len(tests)
    delta = tests[-1]['timestamps'][1] - tests[0]['timestamps'][0]
    return num_tests, delta


def print_summary(stream):
    stream.write("\n======\nTotals\n======\n")
    stream.write("Run: %s in %s sec.\n" % (count_tests('status', '.*'),
                                           run_time()))
    stream.write(" - Passed: %s\n" % count_tests('status', 'success'))
    stream.write(" - Skipped: %s\n" % count_tests('status', 'skip'))
    stream.write(" - Failed: %s\n" % count_tests('status', 'fail'))

    # we could have no results, especially as we filter out the process-codes
    if RESULTS:
        stream.write("\n==============\nWorker Balance\n==============\n")

        for w in range(max(RESULTS.keys()) + 1):
            if w not in RESULTS:
                stream.write(
                    " - WARNING: missing Worker %s! "
                    "Race in testr accounting.\n" % w)
            else:
                num, time = worker_stats(w)
                stream.write(" - Worker %s (%s tests) => %ss\n" %
                             (w, num, time))


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--no-failure-debug', '-n', action='store_true',
                        dest='print_failures', help='Disable printing failure '
                        'debug information in realtime')
    parser.add_argument('--fails', '-f', action='store_true',
                        dest='post_fails', help='Print failure debug '
                        'information after the stream is proccesed')
    return parser.parse_args()


def main():
    args = parse_args()
    stream = subunit.ByteStreamToStreamResult(
        sys.stdin, non_subunit_name='stdout')
    outcomes = testtools.StreamToDict(
        functools.partial(show_outcome, sys.stdout,
                          print_failures=args.print_failures))
    summary = testtools.StreamSummary()
    result = testtools.CopyStreamResult([outcomes, summary])
    result.startTestRun()
    try:
        stream.run(result)
    finally:
        result.stopTestRun()
    if args.post_fails:
        print_fails(sys.stdout)
    print_summary(sys.stdout)
    return (0 if summary.wasSuccessful() else 1)


if __name__ == '__main__':
    sys.exit(main())

#!/usr/bin/env python

# Copyright 2013 IBM Corp.
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

import gzip
import pprint
import re
import StringIO
import sys
import urllib2


pp = pprint.PrettyPrinter()

NOVA_TIMESTAMP = r"\d\d\d\d-\d\d-\d\d \d\d:\d\d:\d\d\.\d\d\d"

NOVA_REGEX = r"(?P<timestamp>%s) (?P<pid>\d+ )?(?P<level>(ERROR|TRACE)) " \
    "(?P<module>[\w\.]+) (?P<msg>.*)" % (NOVA_TIMESTAMP)


class StackTrace(object):
    timestamp = None
    pid = None
    level = ""
    module = ""
    msg = ""

    def __init__(self, timestamp=None, pid=None, level="", module="",
                 msg=""):
        self.timestamp = timestamp
        self.pid = pid
        self.level = level
        self.module = module
        self.msg = msg

    def append(self, msg):
        self.msg = self.msg + msg

    def is_same(self, data):
        return (data['timestamp'] == self.timestamp and
                data['level'] == self.level)

    def not_none(self):
        return self.timestamp is not None

    def __str__(self):
        buff = "<%s %s %s>\n" % (self.timestamp, self.level, self.module)
        for line in self.msg.splitlines():
            buff = buff + line + "\n"
        return buff


def hunt_for_stacktrace(url):
    """Return TRACE or ERROR lines out of logs."""
    req = urllib2.Request(url)
    req.add_header('Accept-Encoding', 'gzip')
    page = urllib2.urlopen(req)
    buf = StringIO.StringIO(page.read())
    f = gzip.GzipFile(fileobj=buf)
    content = f.read()

    traces = []
    trace = StackTrace()
    for line in content.splitlines():
        m = re.match(NOVA_REGEX, line)
        if m:
            data = m.groupdict()
            if trace.not_none() and trace.is_same(data):
                trace.append(data['msg'] + "\n")
            else:
                trace = StackTrace(
                    timestamp=data.get('timestamp'),
                    pid=data.get('pid'),
                    level=data.get('level'),
                    module=data.get('module'),
                    msg=data.get('msg'))

        else:
            if trace.not_none():
                traces.append(trace)
                trace = StackTrace()

    # once more at the end to pick up any stragglers
    if trace.not_none():
        traces.append(trace)

    return traces


def log_url(url, log):
    return "%s/%s" % (url, log)


def collect_logs(url):
    page = urllib2.urlopen(url)
    content = page.read()
    logs = re.findall('(screen-[\w-]+\.txt\.gz)</a>', content)
    return logs


def usage():
    print("""
Usage: find_stack_traces.py <logurl>

Hunts for stack traces in a devstack run. Must provide it a base log url
from a tempest devstack run. Should start with http and end with /logs/.

Returns a report listing stack traces out of the various files where
they are found.
""")
    sys.exit(0)


def print_stats(items, fname, verbose=False):
    errors = len(filter(lambda x: x.level == "ERROR", items))
    traces = len(filter(lambda x: x.level == "TRACE", items))
    print("%d ERRORS found in %s" % (errors, fname))
    print("%d TRACES found in %s" % (traces, fname))

    if verbose:
        for item in items:
            print(item)
        print("\n\n")


def main():
    if len(sys.argv) == 2:
        url = sys.argv[1]
        loglist = collect_logs(url)

        # probably wrong base url
        if not loglist:
            usage()

        for log in loglist:
            logurl = log_url(url, log)
            traces = hunt_for_stacktrace(logurl)

            if traces:
                print_stats(traces, log, verbose=True)

    else:
        usage()

if __name__ == '__main__':
    main()

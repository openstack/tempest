#!/usr/bin/env python
# vim: tabstop=4 shiftwidth=4 softtabstop=4

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
import re
import StringIO
import sys
import urllib2


def hunt_for_stacktrace(url):
    """Return TRACE or ERROR lines out of logs."""
    page = urllib2.urlopen(url)
    buf = StringIO.StringIO(page.read())
    f = gzip.GzipFile(fileobj=buf)
    content = f.read()
    traces = re.findall('^(.*? (TRACE|ERROR) .*?)$', content, re.MULTILINE)
    tracelist = map(lambda x: x[0], traces)
    # filter out log definitions as false possitives
    return filter(lambda x: not re.search('logging_exception_prefix', x),
                  tracelist)


def log_url(url, log):
    return "%s/%s" % (url, log)


def collect_logs(url):
    page = urllib2.urlopen(url)
    content = page.read()
    logs = re.findall('(screen-[\w-]+\.txt\.gz)</a>', content)
    return logs


def usage():
    print """
Usage: find_stack_traces.py <logurl>

Hunts for stack traces in a devstack run. Must provide it a base log url
from a tempest devstack run. Should start with http and end with /logs/.

Returns a report listing stack traces out of the various files where
they are found.
"""
    sys.exit(0)


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
                print "\n\nTRACES found in %s\n" % log
                for line in traces:
                    print line
    else:
        usage()

if __name__ == '__main__':
    main()

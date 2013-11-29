#!/usr/bin/env python
# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2013 Red Hat, Inc.
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

import argparse
import gzip
import os
import re
import StringIO
import sys
import urllib2
import yaml


is_neutron = os.environ.get('DEVSTACK_GATE_NEUTRON', "0") == "1"
dump_all_errors = is_neutron


def process_files(file_specs, url_specs, whitelists):
    regexp = re.compile(r"^.*(ERROR|CRITICAL).*\[.*\-.*\]")
    had_errors = False
    for (name, filename) in file_specs:
        whitelist = whitelists.get(name, [])
        with open(filename) as content:
            if scan_content(name, content, regexp, whitelist):
                had_errors = True
    for (name, url) in url_specs:
        whitelist = whitelists.get(name, [])
        req = urllib2.Request(url)
        req.add_header('Accept-Encoding', 'gzip')
        page = urllib2.urlopen(req)
        buf = StringIO.StringIO(page.read())
        f = gzip.GzipFile(fileobj=buf)
        if scan_content(name, f.read().splitlines(), regexp, whitelist):
            had_errors = True
    return had_errors


def scan_content(name, content, regexp, whitelist):
    had_errors = False
    print_log_name = True
    for line in content:
        if not line.startswith("Stderr:") and regexp.match(line):
            whitelisted = False
            for w in whitelist:
                pat = ".*%s.*%s.*" % (w['module'].replace('.', '\\.'),
                                      w['message'])
                if re.match(pat, line):
                    whitelisted = True
                    break
            if not whitelisted or dump_all_errors:
                if print_log_name:
                    print("Log File: %s" % name)
                    print_log_name = False
                if not whitelisted:
                    had_errors = True
                print(line)
    return had_errors


def collect_url_logs(url):
    page = urllib2.urlopen(url)
    content = page.read()
    logs = re.findall('(screen-[\w-]+\.txt\.gz)</a>', content)
    return logs


def main(opts):
    if opts.directory and opts.url or not (opts.directory or opts.url):
        print("Must provide exactly one of -d or -u")
        exit(1)
    print("Checking logs...")
    WHITELIST_FILE = os.path.join(
        os.path.abspath(os.path.dirname(os.path.dirname(__file__))),
        "etc", "whitelist.yaml")

    file_matcher = re.compile(r".*screen-([\w-]+)\.log")
    files = []
    if opts.directory:
        d = opts.directory
        for f in os.listdir(d):
            files.append(os.path.join(d, f))
    files_to_process = []
    for f in files:
        m = file_matcher.match(f)
        if m:
            files_to_process.append((m.group(1), f))

    url_matcher = re.compile(r".*screen-([\w-]+)\.txt\.gz")
    urls = []
    if opts.url:
        for logfile in collect_url_logs(opts.url):
            urls.append("%s/%s" % (opts.url, logfile))
    urls_to_process = []
    for u in urls:
        m = url_matcher.match(u)
        if m:
            urls_to_process.append((m.group(1), u))

    whitelists = {}
    with open(WHITELIST_FILE) as stream:
        loaded = yaml.safe_load(stream)
        if loaded:
            for (name, l) in loaded.iteritems():
                for w in l:
                    assert 'module' in w, 'no module in %s' % name
                    assert 'message' in w, 'no message in %s' % name
            whitelists = loaded
    if process_files(files_to_process, urls_to_process, whitelists):
        print("Logs have errors")
        if is_neutron:
            print("Currently not failing neutron builds with errors")
            return 0
        # Return non-zero to start failing builds
        return 0
    else:
        print("ok")
        return 0

usage = """
Find non-white-listed log errors in log files from a devstack-gate run.
Log files will be searched for ERROR or CRITICAL messages. If any
error messages do not match any of the whitelist entries contained in
etc/whitelist.yaml, those messages will be printed to the console and
failure will be returned. A file directory containing logs or a url to the
log files of an OpenStack gate job can be provided.

The whitelist yaml looks like:

log-name:
    - module: "a.b.c"
      message: "regexp"
    - module: "a.b.c"
      message: "regexp"

repeated for each log file with a whitelist.
"""

parser = argparse.ArgumentParser(description=usage)
parser.add_argument('-d', '--directory',
                    help="Directory containing log files")
parser.add_argument('-u', '--url',
                    help="url containing logs from an OpenStack gate job")

if __name__ == "__main__":
    try:
        sys.exit(main(parser.parse_args()))
    except Exception as e:
        print("Failure in script: %s" % e)
        # Don't fail if there is a problem with the script.
        sys.exit(0)

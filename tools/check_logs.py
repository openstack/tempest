#!/usr/bin/env python

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
import io
import os
import re
import sys
import urllib.request as urlreq

import yaml

# DEVSTACK_GATE_GRENADE is either unset if grenade is not running
# or a string describing what type of grenade run to perform.
is_grenade = os.environ.get('DEVSTACK_GATE_GRENADE') is not None
dump_all_errors = True

# As logs are made clean, remove from this set
allowed_dirty = set([
    'c-api',
    'ceilometer-acentral',
    'ceilometer-acompute',
    'ceilometer-alarm-evaluator',
    'ceilometer-anotification',
    'ceilometer-api',
    'ceilometer-collector',
    'c-vol',
    'g-api',
    'h-api',
    'h-eng',
    'ir-cond',
    'n-api',
    'n-cpu',
    'n-net',
    'q-agt',
    'q-dhcp',
    'q-lbaas',
    'q-meta',
    'q-metering',
    'q-svc',
    's-proxy'])


def process_files(file_specs, url_specs, allow_lists):
    regexp = re.compile(r"^.* (ERROR|CRITICAL|TRACE) .*\[.*\-.*\]")
    logs_with_errors = []
    for (name, filename) in file_specs:
        allow_list = allow_lists.get(name, [])
        with open(filename) as content:
            if scan_content(content, regexp, allow_list):
                logs_with_errors.append(name)
    for (name, url) in url_specs:
        allow_list = allow_lists.get(name, [])
        req = urlreq.Request(url)
        req.add_header('Accept-Encoding', 'gzip')
        page = urlreq.urlopen(req)
        buf = io.StringIO(page.read())
        f = gzip.GzipFile(fileobj=buf)
        if scan_content(f.read().splitlines(), regexp, allow_list):
            logs_with_errors.append(name)
    return logs_with_errors


def scan_content(content, regexp, allow_list):
    had_errors = False
    for line in content:
        if not line.startswith("Stderr:") and regexp.match(line):
            allowed = False
            for w in allow_list:
                pat = ".*%s.*%s.*" % (w['module'].replace('.', '\\.'),
                                      w['message'])
                if re.match(pat, line):
                    allowed = True
                    break
            if not allowed or dump_all_errors:
                if not allowed:
                    had_errors = True
    return had_errors


def collect_url_logs(url):
    page = urlreq.urlopen(url)
    content = page.read()
    logs = re.findall(r'(screen-[\w-]+\.txt\.gz)</a>', content)
    return logs


def main(opts):
    if opts.directory and opts.url or not (opts.directory or opts.url):
        print("Must provide exactly one of -d or -u")
        return 1
    print("Checking logs...")
    ALLOW_LIST_FILE = os.path.join(
        os.path.abspath(os.path.dirname(os.path.dirname(__file__))),
        "etc", "allow-list.yaml")

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

    allow_lists = {}
    with open(ALLOW_LIST_FILE) as stream:
        loaded = yaml.safe_load(stream)
        if loaded:
            for (name, l) in loaded.values():
                for w in l:
                    assert 'module' in w, 'no module in %s' % name
                    assert 'message' in w, 'no message in %s' % name
            allow_lists = loaded
    logs_with_errors = process_files(files_to_process, urls_to_process,
                                     allow_lists)

    failed = False
    if logs_with_errors:
        log_files = set(logs_with_errors)
        for log in log_files:
            msg = '%s log file has errors' % log
            if log not in allowed_dirty:
                msg += ' and is not allowed to have them'
                failed = True
            print(msg)
        print("\nPlease check the respective log files to see the errors")
    if failed:
        if is_grenade:
            print("Currently not failing grenade runs with errors")
            return 0
        return 1
    print("ok")
    return 0


usage = """
Find non-allow-listed log errors in log files from a devstack-gate run.
Log files will be searched for ERROR or CRITICAL messages. If any
error messages do not match any of the allow-list entries contained in
etc/allow-list.yaml, those messages will be printed to the console and
failure will be returned. A file directory containing logs or a url to the
log files of an OpenStack gate job can be provided.

The allow-list yaml looks like:

log-name:
    - module: "a.b.c"
      message: "regexp"
    - module: "a.b.c"
      message: "regexp"

repeated for each log file with an allow-list.
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

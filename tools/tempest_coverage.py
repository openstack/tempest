# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2012 IBM
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
#    under the License

import json
import os
import re
import shutil
import sys

from tempest.common.rest_client import RestClient
from tempest import config
from tempest.openstack.common import cfg
from tempest.tests.compute import base

CONF = config.TempestConfig()


class CoverageClientJSON(RestClient):

    def __init__(self, config, username, password, auth_url, tenant_name=None):
        super(CoverageClientJSON, self).__init__(config, username, password,
                                                 auth_url, tenant_name)
        self.service = self.config.compute.catalog_type

    def start_coverage(self):
        post_body = {
            'start': {},
        }
        post_body = json.dumps(post_body)
        return self.post('os-coverage/action', post_body, self.headers)

    def start_coverage_combine(self):
        post_body = {
            'start': {
                'combine': True,
            },
        }
        post_body = json.dumps(post_body)
        return self.post('os-coverage/action', post_body, self.headers)

    def stop_coverage(self):
        post_body = {
            'stop': {},
        }
        post_body = json.dumps(post_body)
        resp, body = self.post('os-coverage/action', post_body, self.headers)
        body = json.loads(body)
        return resp, body

    def report_coverage_xml(self, file=None):
        post_body = {
            'report': {
                'file': 'coverage.report',
                'xml': True,
            },
        }
        if file:
            post_body['report']['file'] = file
        post_body = json.dumps(post_body)
        resp, body = self.post('os-coverage/action', post_body, self.headers)
        body = json.loads(body)
        return resp, body

    def report_coverage(self, file=None):
        post_body = {
            'report': {
                'file': 'coverage.report',
            },
        }
        if file:
            post_body['report']['file'] = file
        post_body = json.dumps(post_body)
        resp, body = self.post('os-coverage/action', post_body, self.headers)
        body = json.loads(body)
        return resp, body

    def report_coverage_html(self, file=None):
        post_body = {
            'report': {
                'file': 'coverage.report',
                'html': True,
            },
        }
        if file:
            post_body['report']['file'] = file
        post_body = json.dumps(post_body)
        resp, body = self.post('os-coverage/action', post_body, self.headers)
        body = json.loads(body)
        return resp, body


def parse_opts(argv):
    cli_opts = [
        cfg.StrOpt('command',
                   short='c',
                   default='',
                   help="This required argument is used to specify the "
                        "coverage command to run. Only 'start', "
                        "'stop', or 'report' are valid fields."),
        cfg.StrOpt('filename',
                   default='tempest-coverage',
                   help="Specify a filename to be used for generated report "
                        "files"),
        cfg.BoolOpt('xml',
                    default=False,
                    help='Generate XML reports instead of text'),
        cfg.BoolOpt('html',
                    default=False,
                    help='Generate HTML reports instead of text'),
        cfg.BoolOpt('combine',
                    default=False,
                    help='Generate a single report for all services'),
        cfg.StrOpt('output',
                   short='o',
                   default=None,
                   help='Optional directory to copy generated coverage data or'
                        ' reports into. This directory must not already exist '
                        'it will be created')
    ]
    CLI = cfg.ConfigOpts()
    CLI.register_cli_opts(cli_opts)
    CLI(argv[1:])
    return CLI


def main(argv):
    CLI = parse_opts(argv)
    client_args = (CONF, CONF.identity.admin_username,
                   CONF.identity.admin_password, CONF.identity.uri,
                   CONF.identity.admin_tenant_name)
    coverage_client = CoverageClientJSON(*client_args)

    if CLI.command == 'start':
        if CLI.combine:
            coverage_client.start_coverage_combine()
        else:
            coverage_client.start_coverage()

    elif CLI.command == 'stop':
        resp, body = coverage_client.stop_coverage()
        if not resp['status'] == '200':
            print 'coverage stop failed with: %s:' % (resp['status'] + ': '
                                                      + body)
            exit(int(resp['status']))
        path = body['path']
        if CLI.output:
            shutil.copytree(path, CLI.output)
        else:
            print "Data files located at: %s" % path

    elif CLI.command == 'report':
        if CLI.xml:
            resp, body = coverage_client.report_coverage_xml(file=CLI.filename)
        elif CLI.html:
            resp, body = coverage_client.report_coverage_html(
                                                            file=CLI.filename)
        else:
            resp, body = coverage_client.report_coverage(file=CLI.filename)
        if not resp['status'] == '200':
            print 'coverage report failed with: %s:' % (resp['status'] + ': '
                                                        + body)
            exit(int(resp['status']))
        path = body['path']
        if CLI.output:
            if CLI.html:
                shutil.copytree(path, CLI.output)
            else:
                path = os.path.dirname(path)
                shutil.copytree(path, CLI.output)
        else:
            if not CLI.html:
                path = os.path.dirname(path)
            print 'Report files located at: %s' % path

    else:
        print 'Invalid command'
        exit(1)


if __name__ == "__main__":
    main(sys.argv)

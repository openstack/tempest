# Copyright 2016 Rackspace
#
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

"""
subunit-describe-calls is a parser for subunit streams to determine what REST
API calls are made inside of a test and in what order they are called.

Runtime Arguments
-----------------

* ``--subunit, -s``: (Optional) The path to the subunit file being parsed,
  defaults to stdin
* ``--non-subunit-name, -n``: (Optional) The file_name that the logs are being
  stored in
* ``--output-file, -o``: (Optional) The path where the JSON output will be
  written to. This contains more information than is present in stdout.
* ``--ports, -p``: (Optional) The path to a JSON file describing the ports
  being used by different services
* ``--verbose, -v``: (Optional) Print Request and Response Headers and Body
  data to stdout in the non cliff deprecated CLI
* ``--all-stdout, -a``: (Optional) Print Request and Response Headers and Body
  data to stdout


Usage
-----

subunit-describe-calls will take in either stdin subunit v1 or v2 stream or a
file path which contains either a subunit v1 or v2 stream passed via the
``--subunit`` parameter. This is then parsed checking for details contained in
the file_bytes of the ``--non-subunit-name`` parameter (the default is
pythonlogging which is what Tempest uses to store logs). By default `the
OpenStack default ports
<https://docs.openstack.org/install-guide/firewalls-default-ports.html>`_
are used unless a file is provided via the ``--ports`` option. The resulting
output is dumped in JSON output to the path provided in the ``--output-file``
option.

Ports file JSON structure
^^^^^^^^^^^^^^^^^^^^^^^^^
::

  {
      "<port number>": "<name of service>",
      ...
  }


Output file JSON structure
^^^^^^^^^^^^^^^^^^^^^^^^^^
::

  {
      "full_test_name[with_id_and_tags]": [
          {
              "name": "The ClassName.MethodName that made the call",
              "verb": "HTTP Verb",
              "service": "Name of the service",
              "url": "A shortened version of the URL called",
              "status_code": "The status code of the response",
              "request_headers": "The headers of the request",
              "request_body": "The body of the request",
              "response_headers": "The headers of the response",
              "response_body": "The body of the response"
          }
      ]
  }
"""
import argparse
import collections
import io
import os
import re
import sys
import traceback

from cliff.command import Command
from oslo_serialization import jsonutils as json
import subunit
import testtools


DESCRIPTION = "Outputs all HTTP calls a given test made that were logged."


class UrlParser(testtools.TestResult):

    uuid_re = re.compile(r'(^|[^0-9a-f])[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-'
                         '[0-9a-f]{4}-[0-9a-f]{12}([^0-9a-f]|$)')
    id_re = re.compile(r'(^|[^0-9a-z])[0-9a-z]{8}[0-9a-z]{4}[0-9a-z]{4}'
                       '[0-9a-z]{4}[0-9a-z]{12}([^0-9a-z]|$)')
    ip_re = re.compile(r'(^|[^0-9])[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]'
                       '{1,3}([^0-9]|$)')
    url_re = re.compile(r'.*INFO.*Request \((?P<name>.*)\): (?P<code>[\d]{3}) '
                        r'(?P<verb>\w*) (?P<url>.*) .*')
    port_re = re.compile(r'.*:(?P<port>\d+).*')
    path_re = re.compile(r'http[s]?://[^/]*/(?P<path>.*)')
    request_re = re.compile(r'.* Request - Headers: (?P<headers>.*)')
    response_re = re.compile(r'.* Response - Headers: (?P<headers>.*)')
    body_re = re.compile(r'.*Body: (?P<body>.*)')

    # Based on OpenStack default ports:
    # https://docs.openstack.org/install-guide/firewalls-default-ports.html
    services = {
        "8776": "Block Storage",
        "8774": "Nova",
        "8773": "Nova-API", "8775": "Nova-API",
        "8386": "Sahara",
        "35357": "Keystone", "5000": "Keystone",
        "9292": "Glance", "9191": "Glance",
        "9696": "Neutron",
        "6000": "Swift", "6001": "Swift", "6002": "Swift",
        "8004": "Heat", "8000": "Heat", "8003": "Heat",
        "8777": "Ceilometer",
        "80": "Horizon",
        "8080": "Swift",
        "443": "SSL",
        "873": "rsync",
        "3260": "iSCSI",
        "3306": "MySQL",
        "5672": "AMQP",
        "8082": "murano",
        "8778": "Clustering",
        "8999": "Vitrage",
        "8989": "Mistral"}

    def __init__(self, services=None):
        super(UrlParser, self).__init__()
        self.test_logs = {}
        self.services = services or self.services

    def addSuccess(self, test, details=None):
        output = test.shortDescription() or test.id()
        calls = self.parse_details(details)
        self.test_logs.update({output: calls})

    def addSkip(self, test, err, details=None):
        output = test.shortDescription() or test.id()
        calls = self.parse_details(details)
        self.test_logs.update({output: calls})

    def addError(self, test, err, details=None):
        output = test.shortDescription() or test.id()
        calls = self.parse_details(details)
        self.test_logs.update({output: calls})

    def addFailure(self, test, err, details=None):
        output = test.shortDescription() or test.id()
        calls = self.parse_details(details)
        self.test_logs.update({output: calls})

    def stopTestRun(self):
        super(UrlParser, self).stopTestRun()

    def startTestRun(self):
        super(UrlParser, self).startTestRun()

    def parse_details(self, details):
        if details is None:
            return

        calls = []
        for _, detail in details.items():
            in_request = False
            in_response = False
            current_call = {}
            for line in detail.as_text().split("\n"):
                url_match = self.url_re.match(line)
                request_match = self.request_re.match(line)
                response_match = self.response_re.match(line)
                body_match = self.body_re.match(line)

                if url_match is not None:
                    if current_call != {}:
                        calls.append(current_call.copy())
                        current_call = {}
                        in_request, in_response = False, False
                    current_call.update({
                        "name": url_match.group("name"),
                        "verb": url_match.group("verb"),
                        "status_code": url_match.group("code"),
                        "service": self.get_service(url_match.group("url")),
                        "url": self.url_path(url_match.group("url"))})
                elif request_match is not None:
                    in_request, in_response = True, False
                    current_call.update(
                        {"request_headers": request_match.group("headers")})
                elif in_request and body_match is not None:
                    in_request = False
                    current_call.update(
                        {"request_body": body_match.group(
                            "body")})
                elif response_match is not None:
                    in_request, in_response = False, True
                    current_call.update(
                        {"response_headers": response_match.group(
                            "headers")})
                elif in_response and body_match is not None:
                    in_response = False
                    current_call.update(
                        {"response_body": body_match.group("body")})
            if current_call != {}:
                calls.append(current_call.copy())

        return calls

    def get_service(self, url):
        match = self.port_re.match(url)
        if match is not None:
            return self.services.get(match.group("port"), "Unknown")
        return "Unknown"

    def url_path(self, url):
        match = self.path_re.match(url)
        if match is not None:
            path = match.group("path")
            path = self.uuid_re.sub(r'\1<uuid>\2', path)
            path = self.ip_re.sub(r'\1<ip>\2', path)
            path = self.id_re.sub(r'\1<id>\2', path)
            return path
        return url


class FileAccumulator(testtools.StreamResult):

    def __init__(self, non_subunit_name='pythonlogging'):
        super(FileAccumulator, self).__init__()
        self.route_codes = collections.defaultdict(io.BytesIO)
        self.non_subunit_name = non_subunit_name

    def status(self, **kwargs):
        if kwargs.get('file_name') != self.non_subunit_name:
            return
        file_bytes = kwargs.get('file_bytes')
        if not file_bytes:
            return
        route_code = kwargs.get('route_code')
        stream = self.route_codes[route_code]
        stream.write(file_bytes)


class ArgumentParser(argparse.ArgumentParser):

    def __init__(self):
        desc = DESCRIPTION
        super(ArgumentParser, self).__init__(description=desc)
        self.prog = "subunit-describe-calls"
        _parser_add_args(self)


def parse(stream, non_subunit_name, ports):
    if ports is not None and os.path.exists(ports):
        ports = json.loads(open(ports).read())

    url_parser = UrlParser(ports)
    suite = subunit.ByteStreamToStreamResult(
        stream, non_subunit_name=non_subunit_name)
    result = testtools.StreamToExtendedDecorator(url_parser)
    accumulator = FileAccumulator(non_subunit_name)
    result = testtools.StreamResultRouter(result)
    result.add_rule(accumulator, 'test_id', test_id=None)
    result.startTestRun()
    suite.run(result)

    for bytes_io in accumulator.route_codes.values():  # v1 processing
        bytes_io.seek(0)
        suite = subunit.ProtocolTestCase(bytes_io)
        suite.run(url_parser)
    result.stopTestRun()

    return url_parser


def output(url_parser, output_file, all_stdout):
    if output_file is not None:
        with open(output_file, "w") as outfile:
            outfile.write(json.dumps(url_parser.test_logs))
        return

    for test_name in url_parser.test_logs:
        items = url_parser.test_logs[test_name]
        sys.stdout.write('{0}\n'.format(test_name))
        if not items:
            sys.stdout.write('\n')
            continue
        for item in items:
            sys.stdout.write('\t- {0} {1} request for {2} to {3}\n'.format(
                item.get('status_code'), item.get('verb'),
                item.get('service'), item.get('url')))
            if all_stdout:
                sys.stdout.write('\t\t- request headers: {0}\n'.format(
                    item.get('request_headers')))
                sys.stdout.write('\t\t- request body: {0}\n'.format(
                    item.get('request_body')))
                sys.stdout.write('\t\t- response headers: {0}\n'.format(
                    item.get('response_headers')))
                sys.stdout.write('\t\t- response body: {0}\n'.format(
                    item.get('response_body')))
        sys.stdout.write('\n')


def entry_point(cl_args=None):
    print('Running subunit_describe_calls ...')
    if not cl_args:
        print("Use of: 'subunit-describe-calls' is deprecated, "
              "please use: 'tempest subunit-describe-calls'")
        cl_args = ArgumentParser().parse_args()
    parser = parse(cl_args.subunit, cl_args.non_subunit_name, cl_args.ports)
    output(parser, cl_args.output_file, cl_args.all_stdout)


def _parser_add_args(parser):
    parser.add_argument(
        "-s", "--subunit", metavar="<subunit file>",
        nargs="?", type=argparse.FileType('rb'), default=sys.stdin,
        help="The path to the subunit output file(default:stdin v1/v2 stream)"
    )

    parser.add_argument(
        "-n", "--non-subunit-name", metavar="<non subunit name>",
        default="pythonlogging",
        help="The name used in subunit to describe the file contents."
    )

    parser.add_argument(
        "-o", "--output-file", metavar="<output file>", default=None,
        help="The output file name for the json."
    )

    parser.add_argument(
        "-p", "--ports", metavar="<ports file>", default=None,
        help="A JSON file describing the ports for each service."
    )

    group = parser.add_mutually_exclusive_group()
    # the -v and --verbose command are for the old subunit-describe-calls
    # main() CLI interface.  It does not work with the new
    # tempest subunit-describe-callss CLI. So when the main CLI approach is
    # deleted this argument is not needed.
    group.add_argument(
        "-v", "--verbose", action='store_true', dest='all_stdout',
        help='Add Request and Response header and body data to stdout print.'
             ' NOTE: This argument deprecated and does not work with'
             ' tempest subunit-describe-calls CLI.'
             ' Use new option: "-a", "--all-stdout"'
    )
    group.add_argument(
        "-a", "--all-stdout", action='store_true',
        help="Add Request and Response header and body data to stdout print."
             " Note: this argument work with the subunit-describe-calls and"
             " tempest subunit-describe-calls CLI commands."
    )


class TempestSubunitDescribeCalls(Command):

    def get_parser(self, prog_name):
        parser = super(TempestSubunitDescribeCalls, self).get_parser(prog_name)
        _parser_add_args(parser)
        return parser

    def take_action(self, parsed_args):
        try:
            entry_point(parsed_args)

        except Exception:
            traceback.print_exc()
            raise

    def get_description(self):
        return DESCRIPTION


if __name__ == "__main__":
    entry_point()

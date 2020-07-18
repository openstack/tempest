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

import argparse
from io import StringIO
import os
import shutil
import subprocess
import sys
import tempfile
from unittest import mock
from unittest.mock import patch


from oslo_serialization import jsonutils as json
from tempest.cmd import subunit_describe_calls
from tempest.tests import base


class TestArgumentParser(base.TestCase):
    def test_init(self):
        test_object = subunit_describe_calls.ArgumentParser()
        self.assertEqual("subunit-describe-calls", test_object.prog)
        self.assertEqual(subunit_describe_calls.DESCRIPTION,
                         test_object.description)


class TestUrlParser(base.TestCase):
    services_custom_ports = {
        "18776": "Block Storage",
        "18774": "Nova",
        "18773": "Nova-API",
        "18386": "Sahara",
        "35358": "Keystone",
        "19292": "Glance",
        "19696": "Neutron",
        "16000": "Swift",
        "18004": "Heat",
        "18777": "Ceilometer",
        "10080": "Horizon",
        "18080": "Swift",
        "1873": "rsync",
        "13260": "iSCSI",
        "13306": "MySQL",
        "15672": "AMQP",
        "18082": "murano"}

    def setUp(self):
        super(TestUrlParser, self).setUp()
        self.test_object = subunit_describe_calls.UrlParser()

    def test_get_service_default_ports(self):
        base_url = "http://site.something.com:"
        for port in self.test_object.services:
            url = base_url + port + "/v2/action"
            service = self.test_object.services[port]
            self.assertEqual(service, self.test_object.get_service(url))

    def test_get_service_custom_ports(self):
        self.test_object = subunit_describe_calls.\
            UrlParser(services=self.services_custom_ports)
        base_url = "http://site.something.com:"
        for port in self.services_custom_ports:
            url = base_url + port + "/v2/action"
            service = self.services_custom_ports[port]
            self.assertEqual(service, self.test_object.get_service(url))

    def test_get_service_port_not_found(self):
        url = "https://site.somewhere.com:1234/v2/action"
        self.assertEqual("Unknown", self.test_object.get_service(url))
        self.assertEqual("Unknown", self.test_object.get_service(""))

    def test_parse_details_none(self):
        self.assertIsNone(self.test_object.parse_details(None))

    def test_url_path_ports(self):
        uuid_sample1 = "3715e0bb-b1b3-4291-aa13-2c86c3b9ec93"
        uuid_sample2 = "2715e0bb-b1b4-4291-aa13-2c86c3b9ec88"

        # test http url
        host = "http://host.company.com"
        url = host + ":8776/v3/" + uuid_sample1 + "/types/" + \
            uuid_sample2 + "/extra_specs"
        self.assertEqual("v3/<uuid>/types/<uuid>/extra_specs",
                         self.test_object.url_path(url))
        url = host + ":8774/v2.1/servers/" + uuid_sample1
        self.assertEqual("v2.1/servers/<uuid>",
                         self.test_object.url_path(url))
        # test https url
        host = "https://host.company.com"
        url = host + ":8776/v3/" + uuid_sample1 + "/types/" + \
            uuid_sample2 + "/extra_specs"
        self.assertEqual("v3/<uuid>/types/<uuid>/extra_specs",
                         self.test_object.url_path(url))
        url = host + ":8774/v2.1/servers/" + uuid_sample1
        self.assertEqual("v2.1/servers/<uuid>",
                         self.test_object.url_path(url))

    def test_url_path_no_match(self):
        host_port = 'https://host.company.com:1234/'
        url = 'v2/action/no/special/data'
        self.assertEqual(url, self.test_object.url_path(host_port + url))
        url = 'data'
        self.assertEqual(url, self.test_object.url_path(url))


class TestCliBase(base.TestCase):
    """Base class for share code on all CLI sub-process testing"""

    def setUp(self):
        super(TestCliBase, self).setUp()
        self._subunit_file = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            'subunit_describe_calls_data', 'calls.subunit')

    def _bytes_to_string(self, data):
        if isinstance(data, (bytes, bytearray)):
            data = str(data, 'utf-8')
        return data

    def _assert_cli_message(self, data):
        data = self._bytes_to_string(data)
        self.assertIn("Running subunit_describe_calls ...", data)

    def _assert_deprecated_warning(self, stdout):
        self.assertIn(
            b"Use of: 'subunit-describe-calls' is deprecated, "
            b"please use: 'tempest subunit-describe-calls'", stdout)

    def _assert_expect_json(self, json_data):
        expected_file_name = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            'subunit_describe_calls_data', 'calls_subunit_expected.json')
        with open(expected_file_name, "rb") as read_file:
            expected_result = json.load(read_file)
        self.assertDictEqual(expected_result, json_data)

    def _assert_headers_and_bodies(self, data):
        data = self._bytes_to_string(data)
        self.assertIn('- request headers:', data)
        self.assertIn('- request body:', data)
        self.assertIn('- response headers:', data)
        self.assertIn('- response body:', data)

    def _assert_methods_details(self, data):
        data = self._bytes_to_string(data)
        self.assertIn('foo', data)
        self.assertIn('- 200 POST request for Nova to v2.1/<id>/',
                      data)
        self.assertIn('- 200 DELETE request for Nova to v2.1/<id>/',
                      data)
        self.assertIn('- 200 GET request for Nova to v2.1/<id>/',
                      data)
        self.assertIn('- 404 DELETE request for Nova to v2.1/<id>/',
                      data)

    def _assert_mutual_exclusive_message(self, stderr):
        self.assertIn(b"usage: subunit-describe-calls "
                      b"[-h] [-s [<subunit file>]]", stderr)
        self.assertIn(b"[-n <non subunit name>] [-o <output file>]",
                      stderr)
        self.assertIn(b"[-p <ports file>] [-v | -a]", stderr)
        self.assertIn(
            b"subunit-describe-calls: error: argument -v/--verbose: "
            b"not allowed with argument -a/--all-stdout", stderr)

    def _assert_no_headers_and_bodies(self, data):
        data = self._bytes_to_string(data)
        self.assertNotIn('- request headers:', data)
        self.assertNotIn('- request body:', data)
        self.assertNotIn('- response headers:', data)
        self.assertNotIn('- response body:', data)


class TestMainCli(TestCliBase):
    """Test cases that use subunit_describe_calls module main interface

    via subprocess calls to make sure the total user experience
    is well defined and tested. This interface is deprecated.
    Note: these test do not affect code coverage percentages.
    """

    def test_main_output_file(self):
        temp_file = tempfile.mkstemp()[1]
        p = subprocess.Popen([
            'subunit-describe-calls', '-s', self._subunit_file,
            '-o', temp_file], stdin=subprocess.PIPE,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = p.communicate()
        self.assertEqual(0, p.returncode)
        self._assert_cli_message(stdout)
        self._assert_deprecated_warning(stdout)
        with open(temp_file, 'r') as file:
            data = json.loads(file.read())
        self._assert_expect_json(data)

    def test_main_verbose(self):
        p = subprocess.Popen([
            'subunit-describe-calls', '-s', self._subunit_file,
            '-v'], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE)
        stdout, stderr = p.communicate()
        self.assertEqual(0, p.returncode)
        self._assert_cli_message(stdout)
        self._assert_deprecated_warning(stdout)
        self._assert_methods_details(stdout)
        self._assert_headers_and_bodies(stdout)

    def test_main_all_stdout(self):
        p = subprocess.Popen([
            'subunit-describe-calls', '-s', self._subunit_file,
            '--all-stdout'], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE)
        stdout, stderr = p.communicate()
        self.assertEqual(0, p.returncode)
        self._assert_cli_message(stdout)
        self._assert_deprecated_warning(stdout)
        self._assert_methods_details(stdout)
        self._assert_headers_and_bodies(stdout)

    def test_main(self):
        p = subprocess.Popen([
            'subunit-describe-calls', '-s', self._subunit_file],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE)
        stdout, stderr = p.communicate()
        self.assertEqual(0, p.returncode)
        self._assert_cli_message(stdout)
        self._assert_deprecated_warning(stdout)
        self._assert_methods_details(stdout)
        self._assert_no_headers_and_bodies(stdout)

    def test_main_verbose_and_all_stdout(self):
        p = subprocess.Popen([
            'subunit-describe-calls', '-s', self._subunit_file,
            '-a', '-v'],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE)
        stdout, stderr = p.communicate()
        self.assertEqual(2, p.returncode)
        self._assert_cli_message(stdout)
        self._assert_deprecated_warning(stdout)
        self._assert_mutual_exclusive_message(stderr)


class TestCli(TestCliBase):
    """Test cases that use tempest subunit_describe_calls cliff interface

    via subprocess calls to make sure the total user experience
    is well defined and tested.
    Note: these test do not affect code coverage percentages.
    """

    def _assert_cliff_verbose(self, stdout):
        self.assertIn(b'tempest initialize_app', stdout)
        self.assertIn(b'prepare_to_run_command TempestSubunitDescribeCalls',
                      stdout)
        self.assertIn(b'tempest clean_up TempestSubunitDescribeCalls',
                      stdout)

    def test_run_all_stdout(self):
        p = subprocess.Popen(['tempest', 'subunit-describe-calls',
                              '-s', self._subunit_file, '-a'],
                             stdin=subprocess.PIPE,
                             stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE)
        stdout, stderr = p.communicate()
        self.assertEqual(0, p.returncode)
        self._assert_cli_message(stdout)
        self._assert_methods_details(stdout)
        self._assert_headers_and_bodies(stdout)

    def test_run_verbose(self):
        p = subprocess.Popen(['tempest', 'subunit-describe-calls',
                              '-s', self._subunit_file, '-v'],
                             stdin=subprocess.PIPE,
                             stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE)
        stdout, stderr = p.communicate()
        self.assertEqual(0, p.returncode)
        self._assert_cli_message(stdout)
        self._assert_methods_details(stdout)
        self._assert_no_headers_and_bodies(stdout)
        self._assert_cliff_verbose(stderr)

    def test_run_min(self):
        p = subprocess.Popen(['tempest', 'subunit-describe-calls',
                              '-s', self._subunit_file],
                             stdin=subprocess.PIPE,
                             stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE)
        stdout, stderr = p.communicate()
        self.assertEqual(0, p.returncode)
        self._assert_cli_message(stdout)
        self._assert_methods_details(stdout)
        self._assert_no_headers_and_bodies(stdout)

    def test_run_verbose_all_stdout(self):
        """Test Cliff -v argument

        Since Cliff framework has a argument at the
        abstract command level the -v or --verbose for
        this command is not processed as a boolean.
        So the use of verbose only exists for the
        deprecated main CLI interface.  When the
        main is deleted this test would not be needed.
        """
        p = subprocess.Popen(['tempest', 'subunit-describe-calls',
                              '-s', self._subunit_file, '-a', '-v'],
                             stdin=subprocess.PIPE,
                             stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE)
        stdout, stderr = p.communicate()
        self.assertEqual(0, p.returncode)
        self._assert_cli_message(stdout)
        self._assert_cliff_verbose(stderr)
        self._assert_methods_details(stdout)


class TestSubunitDescribeCalls(TestCliBase):
    """Test cases use the subunit_describe_calls module interface

    and effect code coverage reporting
    """

    def setUp(self):
        super(TestSubunitDescribeCalls, self).setUp()
        self.test_object = subunit_describe_calls.TempestSubunitDescribeCalls(
            app=mock.Mock(),
            app_args=mock.Mock(spec=argparse.Namespace))

    def test_parse(self):
        with open(self._subunit_file, 'r') as read_file:
            parser = subunit_describe_calls.parse(
                read_file, "pythonlogging", None)
        self._assert_expect_json(parser.test_logs)

    def test_get_description(self):
        self.assertEqual(subunit_describe_calls.DESCRIPTION,
                         self.test_object.get_description())

    def test_get_parser_default_min(self):
        parser = self.test_object.get_parser('NAME')
        parsed_args = parser.parse_args([])
        self.assertIsNone(parsed_args.output_file)
        self.assertIsNone(parsed_args.ports)
        self.assertFalse(parsed_args.all_stdout)
        self.assertEqual(parsed_args.subunit, sys.stdin)

    def test_get_parser_default_max(self):
        temp_dir = tempfile.mkdtemp(prefix="parser")
        self.addCleanup(shutil.rmtree, temp_dir, ignore_errors=True)
        outfile_name = os.path.join(temp_dir, 'output.json')
        open(outfile_name, 'a').close()
        portfile_name = os.path.join(temp_dir, 'ports.json')
        open(portfile_name, 'a').close()

        parser = self.test_object.get_parser('NAME')
        parsed_args = parser.parse_args(["-a", "-o " + outfile_name,
                                         "-p " + portfile_name])

        self.assertIsNotNone(parsed_args.output_file)
        self.assertIsNotNone(parsed_args.ports)
        self.assertTrue(parsed_args.all_stdout)
        self.assertEqual(parsed_args.subunit, sys.stdin)

    def test_take_action_min(self):
        parser = self.test_object.get_parser('NAME')
        parsed_args = parser.parse_args(["-s" + self._subunit_file],)
        with patch('sys.stdout', new=StringIO()) as mock_stdout:
            self.test_object.take_action(parsed_args)

        stdout_data = mock_stdout.getvalue()
        self._assert_methods_details(stdout_data)
        self._assert_no_headers_and_bodies(stdout_data)

    def test_take_action_all_stdout(self):
        parser = self.test_object.get_parser('NAME')
        parsed_args = parser.parse_args(["-as" + self._subunit_file],)
        with patch('sys.stdout', new=StringIO()) as mock_stdout:
            self.test_object.take_action(parsed_args)

        stdout_data = mock_stdout.getvalue()
        self._assert_methods_details(stdout_data)
        self._assert_headers_and_bodies(stdout_data)

    def test_take_action_outfile_files(self):
        temp_file = tempfile.mkstemp()[1]
        parser = self.test_object.get_parser('NAME')
        parsed_args = parser.parse_args(
            ["-as" + self._subunit_file, '-o', temp_file], )
        with patch('sys.stdout', new=StringIO()) as mock_stdout:
            self.test_object.take_action(parsed_args)
        stdout_data = mock_stdout.getvalue()
        self._assert_cli_message(stdout_data)
        with open(temp_file, 'r') as file:
            data = json.loads(file.read())
        self._assert_expect_json(data)

    def test_take_action_no_items(self):
        temp_file = tempfile.mkstemp()[1]
        parser = self.test_object.get_parser('NAME')
        parsed_args = parser.parse_args(
            ["-as" + temp_file], )
        with patch('sys.stdout', new=StringIO()) as mock_stdout:
            self.test_object.take_action(parsed_args)
        stdout_data = mock_stdout.getvalue()
        self._assert_cli_message(stdout_data)

    def test_take_action_exception(self):
        parser = self.test_object.get_parser('NAME')
        parsed_args = parser.parse_args(["-s" + self._subunit_file],)
        with patch('sys.stderr', new=StringIO()) as mock_stderr:
            with patch('tempest.cmd.subunit_describe_calls.entry_point') \
                    as mock_method:
                mock_method.side_effect = OSError()
                self.assertRaises(OSError, self.test_object.take_action,
                                  parsed_args)
                stderr_data = mock_stderr.getvalue()

        self.assertIn("Traceback (most recent call last):", stderr_data)
        self.assertIn("entry_point(parsed_args)", stderr_data)

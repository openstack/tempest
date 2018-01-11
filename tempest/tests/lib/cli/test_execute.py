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

import subprocess

import mock

from tempest.lib.cli import base as cli_base
from tempest.lib import exceptions
from tempest.tests import base


class TestExecute(base.TestCase):

    @mock.patch('subprocess.Popen', autospec=True)
    def test_execute_success(self, mock_popen):
        mock_popen.return_value.returncode = 0
        mock_popen.return_value.communicate.return_value = (
            "__init__.py", "")
        result = cli_base.execute("/bin/ls", action="tempest",
                                  flags="-l -a")
        args, kwargs = mock_popen.call_args
        # Check merge_stderr == False
        self.assertEqual(subprocess.PIPE, kwargs['stderr'])
        # Check action and flags are passed
        args = args[0]
        # We just tests that all pieces are passed through, we cannot make
        # assumptions about the order
        self.assertIn("/bin/ls", args)
        self.assertIn("-l", args)
        self.assertIn("-a", args)
        self.assertIn("tempest", args)
        # The result is mocked - checking that the mock was invoked correctly
        self.assertIsInstance(result, str)
        self.assertIn("__init__.py", result)

    @mock.patch('subprocess.Popen', autospec=True)
    def test_execute_failure(self, mock_popen):
        mock_popen.return_value.returncode = 1
        mock_popen.return_value.communicate.return_value = (
            "No such option --foobar", "")
        result = cli_base.execute("/bin/ls", action="tempest.lib",
                                  flags="--foobar", merge_stderr=True,
                                  fail_ok=True)
        args, kwargs = mock_popen.call_args
        # Check the merge_stderr
        self.assertEqual(subprocess.STDOUT, kwargs['stderr'])
        # Check action and flags are passed
        args = args[0]
        # We just tests that all pieces are passed through, we cannot make
        # assumptions about the order
        self.assertIn("/bin/ls", args)
        self.assertIn("--foobar", args)
        self.assertIn("tempest.lib", args)
        # The result is mocked - checking that the mock was invoked correctly
        self.assertIsInstance(result, str)
        self.assertIn("--foobar", result)

    @mock.patch('subprocess.Popen', autospec=True)
    def test_execute_failure_raise_exception(self, mock_popen):
        mock_popen.return_value.returncode = 1
        mock_popen.return_value.communicate.return_value = (
            "No such option --foobar", "")
        self.assertRaises(exceptions.CommandFailed, cli_base.execute,
                          "/bin/ls", action="tempest", flags="--foobar",
                          merge_stderr=True)

    def test_execute_with_prefix(self):
        result = cli_base.execute("env", action="",
                                  prefix="env NEW_VAR=1")
        self.assertIsInstance(result, str)
        self.assertIn("NEW_VAR=1", result)


class TestCLIClient(base.TestCase):

    @mock.patch.object(cli_base, 'execute')
    def test_execute_with_prefix(self, mock_execute):
        cli = cli_base.CLIClient(prefix='env LAC_ALL=C')
        cli.glance('action')
        self.assertEqual(mock_execute.call_count, 1)
        self.assertEqual(mock_execute.call_args[1],
                         {'prefix': 'env LAC_ALL=C'})

    @mock.patch.object(cli_base, 'execute')
    def test_execute_with_domain_name(self, mock_execute):
        cli = cli_base.CLIClient(
            user_domain_name='default',
            project_domain_name='default'
        )
        cli.glance('action')
        self.assertEqual(mock_execute.call_count, 1)
        self.assertIn('--os-user-domain-name default',
                      mock_execute.call_args[0][2])
        self.assertIn('--os-project-domain-name default',
                      mock_execute.call_args[0][2])
        self.assertNotIn('--os-user-domain-id',
                         mock_execute.call_args[0][2])
        self.assertNotIn('--os-project-domain-id',
                         mock_execute.call_args[0][2])

    @mock.patch.object(cli_base, 'execute')
    def test_execute_with_domain_id(self, mock_execute):
        cli = cli_base.CLIClient(
            user_domain_id='default',
            project_domain_id='default'
        )
        cli.glance('action')
        self.assertEqual(mock_execute.call_count, 1)
        self.assertIn('--os-user-domain-id default',
                      mock_execute.call_args[0][2])
        self.assertIn('--os-project-domain-id default',
                      mock_execute.call_args[0][2])
        self.assertNotIn('--os-user-domain-name',
                         mock_execute.call_args[0][2])
        self.assertNotIn('--os-project-domain-name',
                         mock_execute.call_args[0][2])

    @mock.patch.object(cli_base, 'execute')
    def test_execute_with_default_api_version(self, mock_execute):
        cli = cli_base.CLIClient()
        cli.openstack('action')
        self.assertEqual(mock_execute.call_count, 1)
        self.assertNotIn('--os-identity-api-version ',
                         mock_execute.call_args[0][2])

    @mock.patch.object(cli_base, 'execute')
    def test_execute_with_empty_api_version(self, mock_execute):
        cli = cli_base.CLIClient(identity_api_version='')
        cli.openstack('action')
        self.assertEqual(mock_execute.call_count, 1)
        self.assertNotIn('--os-identity-api-version ',
                         mock_execute.call_args[0][2])

    @mock.patch.object(cli_base, 'execute')
    def test_execute_with_explicit_api_version(self, mock_execute):
        cli = cli_base.CLIClient(identity_api_version='0.0')
        cli.openstack('action')
        self.assertEqual(mock_execute.call_count, 1)
        self.assertIn('--os-identity-api-version 0.0 ',
                      mock_execute.call_args[0][2])

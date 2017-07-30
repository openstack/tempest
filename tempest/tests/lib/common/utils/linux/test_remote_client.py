# Copyright 2017 NEC Corporation.
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

import mock

from tempest.lib.common import ssh
from tempest.lib.common.utils.linux import remote_client
from tempest.lib import exceptions as lib_exc
from tempest.tests import base


class FakeServersClient(object):

    def get_console_output(self, server_id):
        return {"output": "fake_output"}


class TestRemoteClient(base.TestCase):

    @mock.patch.object(ssh.Client, 'exec_command', return_value='success')
    def test_exec_command(self, mock_ssh_exec_command):
        client = remote_client.RemoteClient('192.168.1.10', 'username')
        client.exec_command('ls')
        mock_ssh_exec_command.assert_called_once_with(
            'set -eu -o pipefail; PATH=$PATH:/sbin; ls')

    @mock.patch.object(ssh.Client, 'test_connection_auth')
    def test_validate_authentication(self, mock_test_connection_auth):
        client = remote_client.RemoteClient('192.168.1.10', 'username')
        client.validate_authentication()
        mock_test_connection_auth.assert_called_once_with()

    @mock.patch.object(remote_client.LOG, 'debug')
    @mock.patch.object(ssh.Client, 'exec_command')
    def test_debug_ssh_without_console(self, mock_exec_command, mock_debug):
        mock_exec_command.side_effect = lib_exc.SSHTimeout
        server = {'id': 'fake_id'}
        client = remote_client.RemoteClient('192.168.1.10', 'username',
                                            server=server)
        self.assertRaises(lib_exc.SSHTimeout, client.exec_command, 'ls')
        mock_debug.assert_called_with(
            'Caller: %s. Timeout trying to ssh to server %s',
            'TestRemoteClient:test_debug_ssh_without_console', server)

    @mock.patch.object(remote_client.LOG, 'debug')
    @mock.patch.object(ssh.Client, 'exec_command')
    def test_debug_ssh_with_console(self, mock_exec_command, mock_debug):
        mock_exec_command.side_effect = lib_exc.SSHTimeout
        server = {'id': 'fake_id'}
        client = remote_client.RemoteClient('192.168.1.10', 'username',
                                            server=server,
                                            servers_client=FakeServersClient())
        self.assertRaises(lib_exc.SSHTimeout, client.exec_command, 'ls')
        mock_debug.assert_called_with(
            'Console log for server %s: %s', server['id'], 'fake_output')

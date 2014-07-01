# Copyright 2014 OpenStack Foundation
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

import contextlib
import socket
import time

import mock
import testtools

from tempest.common import ssh
from tempest import exceptions
from tempest.tests import base


class TestSshClient(base.TestCase):

    def test_pkey_calls_paramiko_RSAKey(self):
        with contextlib.nested(
            mock.patch('paramiko.RSAKey.from_private_key'),
            mock.patch('cStringIO.StringIO')) as (rsa_mock, cs_mock):
            cs_mock.return_value = mock.sentinel.csio
            pkey = 'mykey'
            ssh.Client('localhost', 'root', pkey=pkey)
            rsa_mock.assert_called_once_with(mock.sentinel.csio)
            cs_mock.assert_called_once_with('mykey')
            rsa_mock.reset_mock()
            cs_mock.reset_mock()
            pkey = mock.sentinel.pkey
            # Shouldn't call out to load a file from RSAKey, since
            # a sentinel isn't a basestring...
            ssh.Client('localhost', 'root', pkey=pkey)
            self.assertEqual(0, rsa_mock.call_count)
            self.assertEqual(0, cs_mock.call_count)

    def _set_ssh_connection_mocks(self):
        client_mock = mock.MagicMock()
        client_mock.connect.return_value = True
        return (self.patch('paramiko.SSHClient'),
                self.patch('paramiko.AutoAddPolicy'),
                client_mock)

    def test_get_ssh_connection(self):
        c_mock, aa_mock, client_mock = self._set_ssh_connection_mocks()
        s_mock = self.patch('time.sleep')

        c_mock.return_value = client_mock
        aa_mock.return_value = mock.sentinel.aa

        # Test normal case for successful connection on first try
        client = ssh.Client('localhost', 'root', timeout=2)
        client._get_ssh_connection(sleep=1)

        aa_mock.assert_called_once_with()
        client_mock.set_missing_host_key_policy.assert_called_once_with(
            mock.sentinel.aa)
        expected_connect = [mock.call(
            'localhost',
            username='root',
            pkey=None,
            key_filename=None,
            look_for_keys=False,
            timeout=10.0,
            password=None
        )]
        self.assertEqual(expected_connect, client_mock.connect.mock_calls)
        self.assertEqual(0, s_mock.call_count)

    def test_get_ssh_connection_two_attemps(self):
        c_mock, aa_mock, client_mock = self._set_ssh_connection_mocks()

        c_mock.return_value = client_mock
        client_mock.connect.side_effect = [
            socket.error,
            mock.MagicMock()
        ]

        client = ssh.Client('localhost', 'root', timeout=1)
        start_time = int(time.time())
        client._get_ssh_connection(sleep=1)
        end_time = int(time.time())
        self.assertLess((end_time - start_time), 4)
        self.assertGreater((end_time - start_time), 1)

    def test_get_ssh_connection_timeout(self):
        c_mock, aa_mock, client_mock = self._set_ssh_connection_mocks()

        c_mock.return_value = client_mock
        client_mock.connect.side_effect = [
            socket.error,
            socket.error,
            socket.error,
        ]

        client = ssh.Client('localhost', 'root', timeout=2)
        start_time = int(time.time())
        with testtools.ExpectedException(exceptions.SSHTimeout):
            client._get_ssh_connection()
        end_time = int(time.time())
        self.assertLess((end_time - start_time), 5)
        self.assertGreaterEqual((end_time - start_time), 2)

    def test_exec_command(self):
        gsc_mock = self.patch('tempest.common.ssh.Client._get_ssh_connection')
        ito_mock = self.patch('tempest.common.ssh.Client._is_timed_out')
        select_mock = self.patch('select.poll')

        client_mock = mock.MagicMock()
        tran_mock = mock.MagicMock()
        chan_mock = mock.MagicMock()
        poll_mock = mock.MagicMock()

        def reset_mocks():
            gsc_mock.reset_mock()
            ito_mock.reset_mock()
            select_mock.reset_mock()
            poll_mock.reset_mock()
            client_mock.reset_mock()
            tran_mock.reset_mock()
            chan_mock.reset_mock()

        select_mock.return_value = poll_mock
        gsc_mock.return_value = client_mock
        ito_mock.return_value = True
        client_mock.get_transport.return_value = tran_mock
        tran_mock.open_session.return_value = chan_mock
        poll_mock.poll.side_effect = [
            [0, 0, 0]
        ]

        # Test for a timeout condition immediately raised
        client = ssh.Client('localhost', 'root', timeout=2)
        with testtools.ExpectedException(exceptions.TimeoutException):
            client.exec_command("test")

        chan_mock.fileno.assert_called_once_with()
        chan_mock.exec_command.assert_called_once_with("test")
        chan_mock.shutdown_write.assert_called_once_with()

        SELECT_POLLIN = 1
        poll_mock.register.assert_called_once_with(chan_mock, SELECT_POLLIN)
        poll_mock.poll.assert_called_once_with(10)

        # Test for proper reading of STDOUT and STDERROR and closing
        # of all file descriptors.

        reset_mocks()

        select_mock.return_value = poll_mock
        gsc_mock.return_value = client_mock
        ito_mock.return_value = False
        client_mock.get_transport.return_value = tran_mock
        tran_mock.open_session.return_value = chan_mock
        poll_mock.poll.side_effect = [
            [1, 0, 0]
        ]
        closed_prop = mock.PropertyMock(return_value=True)
        type(chan_mock).closed = closed_prop
        chan_mock.recv_exit_status.return_value = 0
        chan_mock.recv.return_value = ''
        chan_mock.recv_stderr.return_value = ''

        client = ssh.Client('localhost', 'root', timeout=2)
        client.exec_command("test")

        chan_mock.fileno.assert_called_once_with()
        chan_mock.exec_command.assert_called_once_with("test")
        chan_mock.shutdown_write.assert_called_once_with()

        SELECT_POLLIN = 1
        poll_mock.register.assert_called_once_with(chan_mock, SELECT_POLLIN)
        poll_mock.poll.assert_called_once_with(10)
        chan_mock.recv_ready.assert_called_once_with()
        chan_mock.recv.assert_called_once_with(1024)
        chan_mock.recv_stderr_ready.assert_called_once_with()
        chan_mock.recv_stderr.assert_called_once_with(1024)
        chan_mock.recv_exit_status.assert_called_once_with()
        closed_prop.assert_called_once_with()

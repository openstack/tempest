# vim: tabstop=4 shiftwidth=4 softtabstop=4

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
            cs_mock.rest_mock()
            pkey = mock.sentinel.pkey
            # Shouldn't call out to load a file from RSAKey, since
            # a sentinel isn't a basestring...
            ssh.Client('localhost', 'root', pkey=pkey)
            rsa_mock.assert_not_called()
            cs_mock.assert_not_called()

    def test_get_ssh_connection(self):
        c_mock = self.patch('paramiko.SSHClient')
        aa_mock = self.patch('paramiko.AutoAddPolicy')
        s_mock = self.patch('time.sleep')
        t_mock = self.patch('time.time')

        aa_mock.return_value = mock.sentinel.aa

        def reset_mocks():
            aa_mock.reset_mock()
            c_mock.reset_mock()
            s_mock.reset_mock()
            t_mock.reset_mock()

        # Test normal case for successful connection on first try
        client_mock = mock.MagicMock()
        c_mock.return_value = client_mock
        client_mock.connect.return_value = True

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
        s_mock.assert_not_called()
        t_mock.assert_called_once_with()

        reset_mocks()

        # Test case when connection fails on first two tries and
        # succeeds on third try (this validates retry logic)
        client_mock.connect.side_effect = [socket.error, socket.error, True]
        t_mock.side_effect = [
            1000,  # Start time
            1001,  # Sleep loop 1
            1002   # Sleep loop 2
        ]

        client._get_ssh_connection(sleep=1)

        expected_sleeps = [
            mock.call(1),
            mock.call(1.01)
        ]
        self.assertEqual(expected_sleeps, s_mock.mock_calls)

        reset_mocks()

        # Test case when connection fails on first three tries and
        # exceeds the timeout, so expect to raise a Timeout exception
        client_mock.connect.side_effect = [
            socket.error,
            socket.error,
            socket.error
        ]
        t_mock.side_effect = [
            1000,  # Start time
            1001,  # Sleep loop 1
            1002,  # Sleep loop 2
            1003,  # Sleep loop 3
            1004  # LOG.error() calls time.time()
        ]

        with testtools.ExpectedException(exceptions.SSHTimeout):
            client._get_ssh_connection()

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

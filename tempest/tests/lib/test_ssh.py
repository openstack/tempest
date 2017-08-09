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

import socket

import mock
import six
from six import StringIO
import testtools

from tempest.lib.common import ssh
from tempest.lib import exceptions
from tempest.tests import base
import tempest.tests.utils as utils


class TestSshClient(base.TestCase):

    SELECT_POLLIN = 1

    @mock.patch('paramiko.RSAKey.from_private_key')
    @mock.patch('six.StringIO')
    def test_pkey_calls_paramiko_RSAKey(self, cs_mock, rsa_mock):
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
            port=22,
            username='root',
            pkey=None,
            key_filename=None,
            look_for_keys=False,
            timeout=10.0,
            password=None,
            sock=None
        )]
        self.assertEqual(expected_connect, client_mock.connect.mock_calls)
        self.assertEqual(0, s_mock.call_count)

    def test_get_ssh_connection_over_ssh(self):
        c_mock, aa_mock, client_mock = self._set_ssh_connection_mocks()
        proxy_client_mock = mock.MagicMock()
        proxy_client_mock.connect.return_value = True
        s_mock = self.patch('time.sleep')

        c_mock.side_effect = [client_mock, proxy_client_mock]
        aa_mock.return_value = mock.sentinel.aa

        proxy_client = ssh.Client('proxy-host', 'proxy-user', timeout=2)
        client = ssh.Client('localhost', 'root', timeout=2,
                            proxy_client=proxy_client)
        client._get_ssh_connection(sleep=1)

        aa_mock.assert_has_calls([mock.call(), mock.call()])
        proxy_client_mock.set_missing_host_key_policy.assert_called_once_with(
            mock.sentinel.aa)
        proxy_expected_connect = [mock.call(
            'proxy-host',
            port=22,
            username='proxy-user',
            pkey=None,
            key_filename=None,
            look_for_keys=False,
            timeout=10.0,
            password=None,
            sock=None
        )]
        self.assertEqual(proxy_expected_connect,
                         proxy_client_mock.connect.mock_calls)
        client_mock.set_missing_host_key_policy.assert_called_once_with(
            mock.sentinel.aa)
        expected_connect = [mock.call(
            'localhost',
            port=22,
            username='root',
            pkey=None,
            key_filename=None,
            look_for_keys=False,
            timeout=10.0,
            password=None,
            sock=proxy_client_mock.get_transport().open_session()
        )]
        self.assertEqual(expected_connect, client_mock.connect.mock_calls)
        self.assertEqual(0, s_mock.call_count)

    @mock.patch('time.sleep')
    def test_get_ssh_connection_two_attemps(self, sleep_mock):
        c_mock, aa_mock, client_mock = self._set_ssh_connection_mocks()

        c_mock.return_value = client_mock
        client_mock.connect.side_effect = [
            socket.error,
            mock.MagicMock()
        ]

        client = ssh.Client('localhost', 'root', timeout=1)
        client._get_ssh_connection(sleep=1)
        # We slept 2 seconds: because sleep is "1" and backoff is "1" too
        sleep_mock.assert_called_once_with(2)
        self.assertEqual(2, client_mock.connect.call_count)

    def test_get_ssh_connection_timeout(self):
        c_mock, aa_mock, client_mock = self._set_ssh_connection_mocks()

        timeout = 2
        time_mock = self.patch('time.time')
        time_mock.side_effect = utils.generate_timeout_series(timeout + 1)

        c_mock.return_value = client_mock
        client_mock.connect.side_effect = [
            socket.error,
            socket.error,
            socket.error,
        ]

        client = ssh.Client('localhost', 'root', timeout=timeout)
        # We need to mock LOG here because LOG.info() calls time.time()
        # in order to preprend a timestamp.
        with mock.patch.object(ssh, 'LOG'):
            self.assertRaises(exceptions.SSHTimeout,
                              client._get_ssh_connection)

        # time.time() should be called twice, first to start the timer
        # and then to compute the timedelta
        self.assertEqual(2, time_mock.call_count)

    @mock.patch('select.POLLIN', SELECT_POLLIN, create=True)
    def test_timeout_in_exec_command(self):
        chan_mock, poll_mock, _ = self._set_mocks_for_select([0, 0, 0], True)

        # Test for a timeout condition immediately raised
        client = ssh.Client('localhost', 'root', timeout=2)
        with testtools.ExpectedException(exceptions.TimeoutException):
            client.exec_command("test")

        chan_mock.fileno.assert_called_once_with()
        chan_mock.exec_command.assert_called_once_with("test")
        chan_mock.shutdown_write.assert_called_once_with()

        poll_mock.register.assert_called_once_with(
            chan_mock, self.SELECT_POLLIN)
        poll_mock.poll.assert_called_once_with(10)

    @mock.patch('select.POLLIN', SELECT_POLLIN, create=True)
    def test_exec_command(self):
        chan_mock, poll_mock, select_mock = (
            self._set_mocks_for_select([[1, 0, 0]], True))

        chan_mock.recv_exit_status.return_value = 0
        chan_mock.recv.return_value = b''
        chan_mock.recv_stderr.return_value = b''

        client = ssh.Client('localhost', 'root', timeout=2)
        client.exec_command("test")

        chan_mock.fileno.assert_called_once_with()
        chan_mock.exec_command.assert_called_once_with("test")
        chan_mock.shutdown_write.assert_called_once_with()

        select_mock.assert_called_once_with()
        poll_mock.register.assert_called_once_with(
            chan_mock, self.SELECT_POLLIN)
        poll_mock.poll.assert_called_once_with(10)
        chan_mock.recv_ready.assert_called_once_with()
        chan_mock.recv.assert_called_once_with(1024)
        chan_mock.recv_stderr_ready.assert_called_once_with()
        chan_mock.recv_stderr.assert_called_once_with(1024)
        chan_mock.recv_exit_status.assert_called_once_with()

    def _set_mocks_for_select(self, poll_data, ito_value=False):
        gsc_mock = self.patch('tempest.lib.common.ssh.Client.'
                              '_get_ssh_connection')
        ito_mock = self.patch('tempest.lib.common.ssh.Client._is_timed_out')
        csp_mock = self.patch(
            'tempest.lib.common.ssh.Client._can_system_poll')
        csp_mock.return_value = True

        select_mock = self.patch('select.poll', create=True)
        client_mock = mock.MagicMock()
        tran_mock = mock.MagicMock()
        chan_mock = mock.MagicMock()
        poll_mock = mock.MagicMock()

        select_mock.return_value = poll_mock
        gsc_mock.return_value = client_mock
        ito_mock.return_value = ito_value
        client_mock.get_transport.return_value = tran_mock
        tran_mock.open_session().__enter__.return_value = chan_mock
        if isinstance(poll_data[0], list):
            poll_mock.poll.side_effect = poll_data
        else:
            poll_mock.poll.return_value = poll_data

        return chan_mock, poll_mock, select_mock

    _utf8_string = six.unichr(1071)
    _utf8_bytes = _utf8_string.encode("utf-8")

    @mock.patch('select.POLLIN', SELECT_POLLIN, create=True)
    def test_exec_good_command_output(self):
        chan_mock, poll_mock, _ = self._set_mocks_for_select([1, 0, 0])
        closed_prop = mock.PropertyMock(return_value=True)
        type(chan_mock).closed = closed_prop

        chan_mock.recv_exit_status.return_value = 0
        chan_mock.recv.side_effect = [self._utf8_bytes[0:1],
                                      self._utf8_bytes[1:], b'R', b'']
        chan_mock.recv_stderr.return_value = b''

        client = ssh.Client('localhost', 'root', timeout=2)
        out_data = client.exec_command("test")
        self.assertEqual(self._utf8_string + 'R', out_data)

    @mock.patch('select.POLLIN', SELECT_POLLIN, create=True)
    def test_exec_bad_command_output(self):
        chan_mock, poll_mock, _ = self._set_mocks_for_select([1, 0, 0])
        closed_prop = mock.PropertyMock(return_value=True)
        type(chan_mock).closed = closed_prop

        chan_mock.recv_exit_status.return_value = 1
        chan_mock.recv.return_value = b''
        chan_mock.recv_stderr.side_effect = [b'R', self._utf8_bytes[0:1],
                                             self._utf8_bytes[1:], b'']

        client = ssh.Client('localhost', 'root', timeout=2)
        exc = self.assertRaises(exceptions.SSHExecCommandFailed,
                                client.exec_command, "test")
        self.assertIn('R' + self._utf8_string, six.text_type(exc))

    def test_exec_command_no_select(self):
        gsc_mock = self.patch('tempest.lib.common.ssh.Client.'
                              '_get_ssh_connection')
        csp_mock = self.patch(
            'tempest.lib.common.ssh.Client._can_system_poll')
        csp_mock.return_value = False

        select_mock = self.patch('select.poll', create=True)
        client_mock = mock.MagicMock()
        tran_mock = mock.MagicMock()
        chan_mock = mock.MagicMock()

        # Test for proper reading of STDOUT and STDERROR

        gsc_mock.return_value = client_mock
        client_mock.get_transport.return_value = tran_mock
        tran_mock.open_session().__enter__.return_value = chan_mock
        chan_mock.recv_exit_status.return_value = 0

        std_out_mock = mock.MagicMock(StringIO)
        std_err_mock = mock.MagicMock(StringIO)
        chan_mock.makefile.return_value = std_out_mock
        chan_mock.makefile_stderr.return_value = std_err_mock

        client = ssh.Client('localhost', 'root', timeout=2)
        client.exec_command("test")

        chan_mock.makefile.assert_called_once_with('rb', 1024)
        chan_mock.makefile_stderr.assert_called_once_with('rb', 1024)
        std_out_mock.read.assert_called_once_with()
        std_err_mock.read.assert_called_once_with()
        self.assertFalse(select_mock.called)

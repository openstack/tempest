# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2012 OpenStack Foundation
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


import cStringIO
import select
import socket
import time
import warnings

from tempest import exceptions


with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    import paramiko


class Client(object):

    def __init__(self, host, username, password=None, timeout=300, pkey=None,
                 channel_timeout=10, look_for_keys=False, key_filename=None):
        self.host = host
        self.username = username
        self.password = password
        if isinstance(pkey, basestring):
            pkey = paramiko.RSAKey.from_private_key(
                cStringIO.StringIO(str(pkey)))
        self.pkey = pkey
        self.look_for_keys = look_for_keys
        self.key_filename = key_filename
        self.timeout = int(timeout)
        self.channel_timeout = float(channel_timeout)
        self.buf_size = 1024

    def _get_ssh_connection(self, sleep=1.5, backoff=1.01):
        """Returns an ssh connection to the specified host."""
        _timeout = True
        bsleep = sleep
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(
            paramiko.AutoAddPolicy())
        _start_time = time.time()

        while not self._is_timed_out(_start_time):
            try:
                ssh.connect(self.host, username=self.username,
                            password=self.password,
                            look_for_keys=self.look_for_keys,
                            key_filename=self.key_filename,
                            timeout=self.channel_timeout, pkey=self.pkey)
                _timeout = False
                break
            except (socket.error,
                    paramiko.AuthenticationException):
                time.sleep(bsleep)
                bsleep *= backoff
                continue
        if _timeout:
            raise exceptions.SSHTimeout(host=self.host,
                                        user=self.username,
                                        password=self.password)
        return ssh

    def _is_timed_out(self, start_time):
        return (time.time() - self.timeout) > start_time

    def connect_until_closed(self):
        """Connect to the server and wait until connection is lost."""
        try:
            ssh = self._get_ssh_connection()
            _transport = ssh.get_transport()
            _start_time = time.time()
            _timed_out = self._is_timed_out(_start_time)
            while _transport.is_active() and not _timed_out:
                time.sleep(5)
                _timed_out = self._is_timed_out(_start_time)
            ssh.close()
        except (EOFError, paramiko.AuthenticationException, socket.error):
            return

    def exec_command(self, cmd):
        """
        Execute the specified command on the server.

        Note that this method is reading whole command outputs to memory, thus
        shouldn't be used for large outputs.

        :returns: data read from standard output of the command.
        :raises: SSHExecCommandFailed if command returns nonzero
                 status. The exception contains command status stderr content.
        """
        ssh = self._get_ssh_connection()
        transport = ssh.get_transport()
        channel = transport.open_session()
        channel.fileno()  # Register event pipe
        channel.exec_command(cmd)
        channel.shutdown_write()
        out_data = []
        err_data = []
        poll = select.poll()
        poll.register(channel, select.POLLIN)
        start_time = time.time()

        while True:
            ready = poll.poll(self.channel_timeout)
            if not any(ready):
                if not self._is_timed_out(start_time):
                    continue
                raise exceptions.TimeoutException(
                    "Command: '{0}' executed on host '{1}'.".format(
                        cmd, self.host))
            if not ready[0]:        # If there is nothing to read.
                continue
            out_chunk = err_chunk = None
            if channel.recv_ready():
                out_chunk = channel.recv(self.buf_size)
                out_data += out_chunk,
            if channel.recv_stderr_ready():
                err_chunk = channel.recv_stderr(self.buf_size)
                err_data += err_chunk,
            if channel.closed and not err_chunk and not out_chunk:
                break
        exit_status = channel.recv_exit_status()
        if 0 != exit_status:
            raise exceptions.SSHExecCommandFailed(
                command=cmd, exit_status=exit_status,
                strerror=''.join(err_data))
        return ''.join(out_data)

    def test_connection_auth(self):
        """Returns true if ssh can connect to server."""
        try:
            connection = self._get_ssh_connection()
            connection.close()
        except paramiko.AuthenticationException:
            return False

        return True

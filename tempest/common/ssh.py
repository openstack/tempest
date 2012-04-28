# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2012 OpenStack, LLC
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

import time
import socket
import warnings

from tempest import exceptions


with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    import paramiko


class Client(object):

    def __init__(self, host, username, password=None, timeout=300,
                 channel_timeout=10, look_for_keys=False, key_filename=None):
        self.host = host
        self.username = username
        self.password = password
        self.look_for_keys = look_for_keys
        self.key_filename = key_filename
        self.timeout = int(timeout)
        self.channel_timeout = int(channel_timeout)

    def _get_ssh_connection(self):
        """Returns an ssh connection to the specified host"""
        _timeout = True
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(
            paramiko.AutoAddPolicy())
        _start_time = time.time()

        while not self._is_timed_out(self.timeout, _start_time):
            try:
                ssh.connect(self.host, username=self.username,
                            password=self.password,
                            look_for_keys=self.look_for_keys,
                            key_filename=self.key_filename,
                            timeout=self.timeout)
                _timeout = False
                break
            except socket.error:
                continue
            except paramiko.AuthenticationException:
                time.sleep(5)
                continue
        if _timeout:
            raise exceptions.SSHTimeout(host=self.host,
                                        user=self.username,
                                        password=self.password)
        return ssh

    def _is_timed_out(self, timeout, start_time):
        return (time.time() - timeout) > start_time

    def connect_until_closed(self):
        """Connect to the server and wait until connection is lost"""
        try:
            ssh = self._get_ssh_connection()
            _transport = ssh.get_transport()
            _start_time = time.time()
            _timed_out = self._is_timed_out(self.timeout, _start_time)
            while _transport.is_active() and not _timed_out:
                time.sleep(5)
                _timed_out = self._is_timed_out(self.timeout, _start_time)
            ssh.close()
        except (EOFError, paramiko.AuthenticationException, socket.error):
            return

    def exec_command(self, cmd):
        """Execute the specified command on the server.

        :returns: data read from standard output of the command

        """
        ssh = self._get_ssh_connection()
        stdin, stdout, stderr = ssh.exec_command(cmd)
        stdin.flush()
        stdin.channel.shutdown_write()
        stdout.channel.settimeout(self.channel_timeout)
        status = stdout.channel.recv_exit_status()
        try:
            output = stdout.read()
        except socket.timeout:
            if status == 0:
                return None, status
        ssh.close()
        return status, output

    def test_connection_auth(self):
        """ Returns true if ssh can connect to server"""
        try:
            connection = self._get_ssh_connection()
            connection.close()
        except paramiko.AuthenticationException:
            return False

        return True

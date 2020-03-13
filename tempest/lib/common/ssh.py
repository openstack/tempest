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


import select
import socket
import time
import warnings

from oslo_log import log as logging
import six

from tempest.lib import exceptions


with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    import paramiko


LOG = logging.getLogger(__name__)


class Client(object):

    def __init__(self, host, username, password=None, timeout=300, pkey=None,
                 channel_timeout=10, look_for_keys=False, key_filename=None,
                 port=22, proxy_client=None):
        """SSH client.

        Many of parameters are just passed to the underlying implementation
        as it is.  See the paramiko documentation for more details.
        http://docs.paramiko.org/en/2.1/api/client.html#paramiko.client.SSHClient.connect

        :param host: Host to login.
        :param username: SSH username.
        :param password: SSH password, or a password to unlock private key.
        :param timeout: Timeout in seconds, including retries.
            Default is 300 seconds.
        :param pkey: Private key.
        :param channel_timeout: Channel timeout in seconds, passed to the
            paramiko.  Default is 10 seconds.
        :param look_for_keys: Whether or not to search for private keys
            in ``~/.ssh``.  Default is False.
        :param key_filename: Filename for private key to use.
        :param port: SSH port number.
        :param proxy_client: Another SSH client to provide a transport
            for ssh-over-ssh.  The default is None, which means
            not to use ssh-over-ssh.
        :type proxy_client: ``tempest.lib.common.ssh.Client`` object
        """
        self.host = host
        self.username = username
        self.port = port
        self.password = password
        if isinstance(pkey, six.string_types):
            pkey = paramiko.RSAKey.from_private_key(
                six.StringIO(str(pkey)))
        self.pkey = pkey
        self.look_for_keys = look_for_keys
        self.key_filename = key_filename
        self.timeout = int(timeout)
        self.channel_timeout = float(channel_timeout)
        self.buf_size = 1024
        self.proxy_client = proxy_client
        if (self.proxy_client and self.proxy_client.host == self.host and
                self.proxy_client.port == self.port and
                self.proxy_client.username == self.username):
            raise exceptions.SSHClientProxyClientLoop(
                host=self.host, port=self.port, username=self.username)
        self._proxy_conn = None

    def _get_ssh_connection(self, sleep=1.5, backoff=1):
        """Returns an ssh connection to the specified host."""
        bsleep = sleep
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(
            paramiko.AutoAddPolicy())
        _start_time = time.time()
        if self.pkey is not None:
            LOG.info("Creating ssh connection to '%s:%d' as '%s'"
                     " with public key authentication",
                     self.host, self.port, self.username)
        else:
            LOG.info("Creating ssh connection to '%s:%d' as '%s'"
                     " with password %s",
                     self.host, self.port, self.username, str(self.password))
        attempts = 0
        while True:
            if self.proxy_client is not None:
                proxy_chan = self._get_proxy_channel()
            else:
                proxy_chan = None
            try:
                ssh.connect(self.host, port=self.port, username=self.username,
                            password=self.password,
                            look_for_keys=self.look_for_keys,
                            key_filename=self.key_filename,
                            timeout=self.channel_timeout, pkey=self.pkey,
                            sock=proxy_chan)
                LOG.info("ssh connection to %s@%s successfully created",
                         self.username, self.host)
                return ssh
            except (EOFError,
                    socket.error, socket.timeout,
                    paramiko.SSHException) as e:
                ssh.close()
                if self._is_timed_out(_start_time):
                    LOG.exception("Failed to establish authenticated ssh"
                                  " connection to %s@%s after %d attempts. "
                                  "Proxy client: %s",
                                  self.username, self.host, attempts,
                                  self._get_proxy_client_info())
                    raise exceptions.SSHTimeout(host=self.host,
                                                user=self.username,
                                                password=self.password)
                bsleep += backoff
                attempts += 1
                LOG.warning("Failed to establish authenticated ssh"
                            " connection to %s@%s (%s). Number attempts: %s."
                            " Retry after %d seconds.",
                            self.username, self.host, e, attempts, bsleep)
                time.sleep(bsleep)

    def _is_timed_out(self, start_time):
        return (time.time() - self.timeout) > start_time

    @staticmethod
    def _can_system_poll():
        return hasattr(select, 'poll')

    def exec_command(self, cmd, encoding="utf-8"):
        """Execute the specified command on the server

        Note that this method is reading whole command outputs to memory, thus
        shouldn't be used for large outputs.

        :param str cmd: Command to run at remote server.
        :param str encoding: Encoding for result from paramiko.
                             Result will not be decoded if None.
        :returns: data read from standard output of the command.
        :raises: SSHExecCommandFailed if command returns nonzero
                 status. The exception contains command status stderr content.
        :raises: TimeoutException if cmd doesn't end when timeout expires.
        """
        ssh = self._get_ssh_connection()
        transport = ssh.get_transport()
        with transport.open_session() as channel:
            channel.fileno()  # Register event pipe
            channel.exec_command(cmd)
            channel.shutdown_write()

            # If the executing host is linux-based, poll the channel
            if self._can_system_poll():
                out_data_chunks = []
                err_data_chunks = []
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
                    if not ready[0]:  # If there is nothing to read.
                        continue
                    out_chunk = err_chunk = None
                    if channel.recv_ready():
                        out_chunk = channel.recv(self.buf_size)
                        out_data_chunks += out_chunk,
                    if channel.recv_stderr_ready():
                        err_chunk = channel.recv_stderr(self.buf_size)
                        err_data_chunks += err_chunk,
                    if not err_chunk and not out_chunk:
                        break
                out_data = b''.join(out_data_chunks)
                err_data = b''.join(err_data_chunks)
            # Just read from the channels
            else:
                out_file = channel.makefile('rb', self.buf_size)
                err_file = channel.makefile_stderr('rb', self.buf_size)
                out_data = out_file.read()
                err_data = err_file.read()
            if encoding:
                out_data = out_data.decode(encoding)
                err_data = err_data.decode(encoding)

            exit_status = channel.recv_exit_status()

        ssh.close()

        if 0 != exit_status:
            raise exceptions.SSHExecCommandFailed(
                command=cmd, exit_status=exit_status,
                stderr=err_data, stdout=out_data)
        return out_data

    def test_connection_auth(self):
        """Raises an exception when we can not connect to server via ssh."""
        connection = self._get_ssh_connection()
        connection.close()

    def _get_proxy_channel(self):
        conn = self.proxy_client._get_ssh_connection()
        # Keep a reference to avoid g/c
        # https://github.com/paramiko/paramiko/issues/440
        self._proxy_conn = conn
        transport = conn.get_transport()
        chan = transport.open_session()
        cmd = 'nc %s %s' % (self.host, self.port)
        chan.exec_command(cmd)
        return chan

    def _get_proxy_client_info(self):
        if not self.proxy_client:
            return 'no proxy client'
        nested_pclient = self.proxy_client._get_proxy_client_info()
        return ('%(username)s@%(host)s:%(port)s, nested proxy client: '
                '%(nested_pclient)s' % {'username': self.proxy_client.username,
                                        'host': self.proxy_client.host,
                                        'port': self.proxy_client.port,
                                        'nested_pclient': nested_pclient})

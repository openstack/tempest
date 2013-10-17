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
import random
import select
import socket
import time
import warnings

import six

from tempest import exceptions
from tempest.openstack.common import log as logging


try:
    import SocketServer
except ImportError:
    import socketserver as SocketServer

with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    import paramiko


LOG = logging.getLogger(__name__)


class Client(SocketServer.BaseRequestHandler):

    def __init__(self, host, username, password=None, timeout=300, pkey=None,
                 channel_timeout=10, look_for_keys=False, key_filename=None,
                 gws=None):
        """
        Added this parameter for creating ssh tunnel, it is a list
        of dictionaries describing each "hop" inside the tunnel.
        The first hop should have a (public) ip reachable from
        the machine that is running the tempest test.
        Also, every hop should be reachable by the previous hop.
        Example of the dictionary:
        gw = {
            "username": user_name,
             "ip": ip,
             "password": password,
             "pkey": <the public key>,
             "key_filename": <file name of the key, it can be set to None>
            }
        # GW variables
            self.GWs = gws
            self.tunnels = []
            self.ssh_gw = None
        """
        self.host = host
        self.username = username
        self.password = password
        self.pkey = self._fix_pkey(pkey)
        self.look_for_keys = look_for_keys
        self.key_filename = key_filename
        self.timeout = int(timeout)
        self.channel_timeout = float(channel_timeout)
        self.buf_size = 1024
        self.host_dict = {
            "username": self.username,
            "ip": self.host,
            "password": self.password,
            "pkey": self.pkey,
            "key_filename": self.key_filename
        }

        # GW variables
        self.GWs = gws
        self.tunnels = []
        self.ssh_gw = None

    def _get_ssh_connection(self, sleep=1.5, backoff=1):
        """Returns an ssh connection to the specified host."""
        bsleep = sleep
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(
            paramiko.AutoAddPolicy())

        _start_time = time.time()
        if self.pkey:
            LOG.info("Creating ssh connection to '%s' as '%s'"
                     " with public key authentication",
                     self.host, self.username)
        else:
            LOG.info("Creating ssh connection to '%s' as '%s'"
                     " with password %s",
                     self.host, self.username, str(self.password))
        attempts = 0
        while True:
            try:
                if self.GWs:
                    ssh = self._build_tunnel()
                else:
                    ssh = self._do_connect(self.host_dict, tunnel=False)

                LOG.info("ssh connection to %s@%s successfully created",
                         self.username, self.host)

                return ssh
            except (socket.error,
                    paramiko.SSHException) as e:
                if self._is_timed_out(_start_time):
                    LOG.exception("Failed to establish authenticated ssh"
                                  " connection to %s@%s after %d attempts",
                                  self.username, self.host, attempts)
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

    def _build_tunnel(self):
        """
         Builds a ssh inception tunneling with
         through GW added tot he list of GWs
        """
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(
            paramiko.AutoAddPolicy())

        # First we need to setup a direct connection
        # to the GW machine with public IP
        gw = self.GWs[0]
        gw["pkey"] = self._fix_pkey(gw["pkey"])
        ssh = self._do_connect(gw, tunnel=False)
        self.tunnels.append(ssh)

        for dest in self.GWs[1:]:

                dest["pkey"] = self._fix_pkey(dest["pkey"])
                ssh = self._do_connect(dest)
                self.tunnels.append(ssh)

        ssh = self._do_connect(self.host_dict)
        return ssh

    def _do_connect(self, dest, tunnel=True):
        """
        Function the wraps the different "connects" that could appear
        :param dest: dictionary with the details of the destination machine
        :param tunnel: if its a tunneled connection
        :return: returns the ssh paramiko client created
        """
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(
            paramiko.AutoAddPolicy())
        try:
            if tunnel:
                LOG.info('Connecting through the tunnel')
                transport = self.tunnels[-1].get_transport()
                dest_addr = (dest["ip"], 22)
                local_addr = ('127.0.0.1', self._get_local_unused_tcp_port())
                channel = transport.open_channel("direct-tcpip",
                                                 dest_addr,
                                                 local_addr)
                hostname = 'localhost'
            else:
                hostname = dest["ip"]
                channel = None

            ssh.connect(hostname=hostname, username=dest["username"],
                        password=dest["password"],
                        look_for_keys=self.look_for_keys,
                        key_filename=dest["key_filename"],
                        timeout=self.channel_timeout,
                        pkey=dest["pkey"], sock=channel)

            LOG.info("Connection %s@%s successfully created",
                     dest["username"], dest["ip"])
        except (socket.error,
                paramiko.SSHException):
                    raise
        return ssh

    def _is_timed_out(self, start_time, timeout=0):
        """
        :param start_time: time when the process starts
        :param timeout: optional value, used if we want
        to use a different timeout
        rather than the "class" timeout,
        for instance giving a timeout to a particular command
        :return: True if the timeout is surpassed
        """
        if timeout is 0:
            timeout = self.timeout
        return (time.time() - timeout) > start_time

    @staticmethod
    def _get_local_unused_tcp_port():
        port = random.randrange(10000, 65535)
        s = socket.socket()
        attempts = 0
        while attempts < 10:
            try:
                LOG.debug("is port %d free?" % port)
                s.connect(('127.0.0.1', port))
                s.shutdown()

                LOG.debug("port %d is not free" % port)
                attempts += 1
            except Exception:
                # port is unused
                LOG.info("port %d is free" % port)
                return port

    @staticmethod
    def _fix_pkey(pkey):
        if isinstance(pkey, six.string_types):
            pkey = paramiko.RSAKey.from_private_key(
                cStringIO.StringIO(str(pkey)))
        return pkey

    def exec_command(self, cmd, cmd_timeout=0):
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
        LOG.info("executing cmd: %s" % cmd)
        while True:
            ready = poll.poll(self.channel_timeout)
            if not any(ready) or cmd_timeout is not 0:
                if not self._is_timed_out(start_time, cmd_timeout):
                    continue
                raise exceptions.TimeoutException(
                    "Command: '{0}' executed on host '{1}'.".format(
                        cmd, self.host))
            if not ready[0]:  # If there is nothing to read.
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
            # hack for avoiding unexpected hung
            time.sleep(0.1)
        exit_status = channel.recv_exit_status()
        if 0 != exit_status:
            raise exceptions.SSHExecCommandFailed(
                command=cmd, exit_status=exit_status,
                strerror=''.join(err_data))
        return ''.join(out_data)

    def test_connection_auth(self):
        """Raises an exception when we can not connect to server via ssh."""
        connection = self._get_ssh_connection()
        connection.close()

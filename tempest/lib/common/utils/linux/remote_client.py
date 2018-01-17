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

import functools
import sys

import netaddr
from oslo_log import log as logging
import six

from tempest.lib.common import ssh
from tempest.lib.common.utils import test_utils
import tempest.lib.exceptions

LOG = logging.getLogger(__name__)


def debug_ssh(function):
    """Decorator to generate extra debug info in case off SSH failure"""
    @functools.wraps(function)
    def wrapper(self, *args, **kwargs):
        try:
            return function(self, *args, **kwargs)
        except Exception as e:
            caller = test_utils.find_test_caller() or "not found"
            if not isinstance(e, tempest.lib.exceptions.SSHTimeout):
                message = ('Executing command on %(ip)s failed. '
                           'Error: %(error)s' % {'ip': self.ip_address,
                                                 'error': e})
                message = '(%s) %s' % (caller, message)
                LOG.error(message)
                raise
            else:
                try:
                    original_exception = sys.exc_info()
                    if self.server:
                        msg = 'Caller: %s. Timeout trying to ssh to server %s'
                        LOG.debug(msg, caller, self.server)
                        if self.console_output_enabled and self.servers_client:
                            try:
                                msg = 'Console log for server %s: %s'
                                console_log = (
                                    self.servers_client.get_console_output(
                                        self.server['id'])['output'])
                                LOG.debug(msg, self.server['id'], console_log)
                            except Exception:
                                msg = 'Could not get console_log for server %s'
                                LOG.debug(msg, self.server['id'])
                    # re-raise the original ssh timeout exception
                    six.reraise(*original_exception)
                finally:
                    # Delete the traceback to avoid circular references
                    _, _, trace = original_exception
                    del trace
    return wrapper


class RemoteClient(object):

    def __init__(self, ip_address, username, password=None, pkey=None,
                 server=None, servers_client=None, ssh_timeout=300,
                 connect_timeout=60, console_output_enabled=True,
                 ssh_shell_prologue="set -eu -o pipefail; PATH=$PATH:/sbin;",
                 ping_count=1, ping_size=56):
        """Executes commands in a VM over ssh

        :param ip_address: IP address to ssh to
        :param username: Ssh username
        :param password: Ssh password
        :param pkey: Ssh public key
        :param server: Server dict, used for debugging purposes
        :param servers_client: Servers client, used for debugging purposes
        :param ssh_timeout: Timeout in seconds to wait for the ssh banner
        :param connect_timeout: Timeout in seconds to wait for TCP connection
        :param console_output_enabled: Support serial console output?
        :param ssh_shell_prologue: Shell fragments to use before command
        :param ping_count: Number of ping packets
        :param ping_size: Packet size for ping packets
        """
        self.server = server
        self.servers_client = servers_client
        self.ip_address = ip_address
        self.console_output_enabled = console_output_enabled
        self.ssh_shell_prologue = ssh_shell_prologue
        self.ping_count = ping_count
        self.ping_size = ping_size

        self.ssh_client = ssh.Client(ip_address, username, password,
                                     ssh_timeout, pkey=pkey,
                                     channel_timeout=connect_timeout)

    @debug_ssh
    def exec_command(self, cmd):
        # Shell options below add more clearness on failures,
        # path is extended for some non-cirros guest oses (centos7)
        cmd = self.ssh_shell_prologue + " " + cmd
        LOG.debug("Remote command: %s", cmd)
        return self.ssh_client.exec_command(cmd)

    @debug_ssh
    def validate_authentication(self):
        """Validate ssh connection and authentication

           This method raises an Exception when the validation fails.
        """
        self.ssh_client.test_connection_auth()

    def ping_host(self, host, count=None, size=None, nic=None):
        if count is None:
            count = self.ping_count
        if size is None:
            size = self.ping_size

        addr = netaddr.IPAddress(host)
        cmd = 'ping6' if addr.version == 6 else 'ping'
        if nic:
            cmd = 'sudo {cmd} -I {nic}'.format(cmd=cmd, nic=nic)
        cmd += ' -c{0} -w{0} -s{1} {2}'.format(count, size, host)
        return self.exec_command(cmd)

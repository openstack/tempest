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

import netaddr
import re
import six
import sys
import time

from oslo_log import log as logging

from tempest import config
from tempest import exceptions
from tempest.lib.common import ssh
from tempest.lib.common.utils import misc as misc_utils
import tempest.lib.exceptions

CONF = config.CONF

LOG = logging.getLogger(__name__)


def debug_ssh(function):
    """Decorator to generate extra debug info in case off SSH failure"""
    def wrapper(self, *args, **kwargs):
        try:
            return function(self, *args, **kwargs)
        except tempest.lib.exceptions.SSHTimeout:
            try:
                original_exception = sys.exc_info()
                caller = misc_utils.find_test_caller() or "not found"
                if self.server:
                    msg = 'Caller: %s. Timeout trying to ssh to server %s'
                    LOG.debug(msg, caller, self.server)
                    if self.log_console and self.servers_client:
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
                 server=None, servers_client=None):
        """Executes commands in a VM over ssh

        :param ip_address: IP address to ssh to
        :param username: ssh username
        :param password: ssh password (optional)
        :param pkey: ssh public key (optional)
        :param server: server dict, used for debugging purposes
        :param servers_client: servers client, used for debugging purposes
        """
        self.server = server
        self.servers_client = servers_client
        ssh_timeout = CONF.validation.ssh_timeout
        connect_timeout = CONF.validation.connect_timeout
        self.log_console = CONF.compute_feature_enabled.console_output

        self.ssh_client = ssh.Client(ip_address, username, password,
                                     ssh_timeout, pkey=pkey,
                                     channel_timeout=connect_timeout)

    @debug_ssh
    def exec_command(self, cmd):
        # Shell options below add more clearness on failures,
        # path is extended for some non-cirros guest oses (centos7)
        cmd = CONF.validation.ssh_shell_prologue + " " + cmd
        LOG.debug("Remote command: %s" % cmd)
        return self.ssh_client.exec_command(cmd)

    @debug_ssh
    def validate_authentication(self):
        """Validate ssh connection and authentication

           This method raises an Exception when the validation fails.
        """
        self.ssh_client.test_connection_auth()

    def hostname_equals_servername(self, expected_hostname):
        # Get host name using command "hostname"
        actual_hostname = self.exec_command("hostname").rstrip()
        return expected_hostname == actual_hostname

    def get_ram_size_in_mb(self):
        output = self.exec_command('free -m | grep Mem')
        if output:
            return output.split()[1]

    def get_number_of_vcpus(self):
        output = self.exec_command('grep -c ^processor /proc/cpuinfo')
        return int(output)

    def get_partitions(self):
        # Return the contents of /proc/partitions
        command = 'cat /proc/partitions'
        output = self.exec_command(command)
        return output

    def get_boot_time(self):
        cmd = 'cut -f1 -d. /proc/uptime'
        boot_secs = self.exec_command(cmd)
        boot_time = time.time() - int(boot_secs)
        return time.localtime(boot_time)

    def write_to_console(self, message):
        message = re.sub("([$\\`])", "\\\\\\\\\\1", message)
        # usually to /dev/ttyS0
        cmd = 'sudo sh -c "echo \\"%s\\" >/dev/console"' % message
        return self.exec_command(cmd)

    def ping_host(self, host, count=CONF.validation.ping_count,
                  size=CONF.validation.ping_size, nic=None):
        addr = netaddr.IPAddress(host)
        cmd = 'ping6' if addr.version == 6 else 'ping'
        if nic:
            cmd = 'sudo {cmd} -I {nic}'.format(cmd=cmd, nic=nic)
        cmd += ' -c{0} -w{0} -s{1} {2}'.format(count, size, host)
        return self.exec_command(cmd)

    def set_mac_address(self, nic, address):
        self.set_nic_state(nic=nic, state="down")
        cmd = "sudo ip link set dev {0} address {1}".format(nic, address)
        self.exec_command(cmd)
        self.set_nic_state(nic=nic, state="up")

    def get_mac_address(self, nic=""):
        show_nic = "show {nic} ".format(nic=nic) if nic else ""
        cmd = "ip addr %s| awk '/ether/ {print $2}'" % show_nic
        return self.exec_command(cmd).strip().lower()

    def get_nic_name_by_mac(self, address):
        cmd = "ip -o link | awk '/%s/ {print $2}'" % address
        nic = self.exec_command(cmd)
        return nic.strip().strip(":").lower()

    def get_nic_name_by_ip(self, address):
        cmd = "ip -o addr | awk '/%s/ {print $2}'" % address
        nic = self.exec_command(cmd)
        return nic.strip().strip(":").lower()

    def get_ip_list(self):
        cmd = "ip address"
        return self.exec_command(cmd)

    def assign_static_ip(self, nic, addr):
        cmd = "sudo ip addr add {ip}/{mask} dev {nic}".format(
            ip=addr, mask=CONF.network.project_network_mask_bits,
            nic=nic
        )
        return self.exec_command(cmd)

    def set_nic_state(self, nic, state="up"):
        cmd = "sudo ip link set {nic} {state}".format(nic=nic, state=state)
        return self.exec_command(cmd)

    def get_pids(self, pr_name):
        # Get pid(s) of a process/program
        cmd = "ps -ef | grep %s | grep -v 'grep' | awk {'print $1'}" % pr_name
        return self.exec_command(cmd).split('\n')

    def get_dns_servers(self):
        cmd = 'cat /etc/resolv.conf'
        resolve_file = self.exec_command(cmd).strip().split('\n')
        entries = (l.split() for l in resolve_file)
        dns_servers = [l[1] for l in entries
                       if len(l) and l[0] == 'nameserver']
        return dns_servers

    def send_signal(self, pid, signum):
        cmd = 'sudo /bin/kill -{sig} {pid}'.format(pid=pid, sig=signum)
        return self.exec_command(cmd)

    def _renew_lease_udhcpc(self, fixed_ip=None):
        """Renews DHCP lease via udhcpc client. """
        file_path = '/var/run/udhcpc.'
        nic_name = self.get_nic_name_by_ip(fixed_ip)
        pid = self.exec_command('cat {path}{nic}.pid'.
                                format(path=file_path, nic=nic_name))
        pid = pid.strip()
        self.send_signal(pid, 'USR1')

    def _renew_lease_dhclient(self, fixed_ip=None):
        """Renews DHCP lease via dhclient client. """
        cmd = "sudo /sbin/dhclient -r && sudo /sbin/dhclient"
        self.exec_command(cmd)

    def renew_lease(self, fixed_ip=None):
        """Wrapper method for renewing DHCP lease via given client

        Supporting:
        * udhcpc
        * dhclient
        """
        # TODO(yfried): add support for dhcpcd
        supported_clients = ['udhcpc', 'dhclient']
        dhcp_client = CONF.scenario.dhcp_client
        if dhcp_client not in supported_clients:
            raise exceptions.InvalidConfiguration('%s DHCP client unsupported'
                                                  % dhcp_client)
        if dhcp_client == 'udhcpc' and not fixed_ip:
            raise ValueError("need to set 'fixed_ip' for udhcpc client")
        return getattr(self, '_renew_lease_' + dhcp_client)(fixed_ip=fixed_ip)

    def mount(self, dev_name, mount_path='/mnt'):
        cmd_mount = 'sudo mount /dev/%s %s' % (dev_name, mount_path)
        self.exec_command(cmd_mount)

    def umount(self, mount_path='/mnt'):
        self.exec_command('sudo umount %s' % mount_path)

    def make_fs(self, dev_name, fs='ext4'):
        cmd_mkfs = 'sudo /usr/sbin/mke2fs -t %s /dev/%s' % (fs, dev_name)
        try:
            self.exec_command(cmd_mkfs)
        except tempest.lib.exceptions.SSHExecCommandFailed:
            LOG.error("Couldn't mke2fs")
            cmd_why = 'sudo ls -lR /dev'
            LOG.info("Contents of /dev: %s" % self.exec_command(cmd_why))
            raise

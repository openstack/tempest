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

import re
import time

from oslo_log import log as logging

from tempest import config
from tempest.lib.common.utils.linux import remote_client
import tempest.lib.exceptions

CONF = config.CONF

LOG = logging.getLogger(__name__)


class RemoteClient(remote_client.RemoteClient):

    # TODO(oomichi): Make this class deprecated after migrating
    #                necessary methods to tempest.lib and cleaning
    #                unnecessary methods up from this class.
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
        super(RemoteClient, self).__init__(
            ip_address, username, password=password, pkey=pkey,
            server=server, servers_client=servers_client,
            ssh_timeout=CONF.validation.ssh_timeout,
            connect_timeout=CONF.validation.connect_timeout,
            console_output_enabled=CONF.compute_feature_enabled.console_output,
            ssh_shell_prologue=CONF.validation.ssh_shell_prologue,
            ping_count=CONF.validation.ping_count,
            ping_size=CONF.validation.ping_size)

    # Note that this method will not work on SLES11 guests, as they do
    # not support the TYPE column on lsblk
    def get_disks(self):
        # Select root disk devices as shown by lsblk
        command = 'lsblk -lb --nodeps'
        output = self.exec_command(command)
        selected = []
        pos = None
        for l in output.splitlines():
            if pos is None and l.find("TYPE") > 0:
                pos = l.find("TYPE")
                # Show header line too
                selected.append(l)
            # lsblk lists disk type in a column right-aligned with TYPE
            elif pos is not None and pos > 0 and l[pos:pos + 4] == "disk":
                selected.append(l)

        if selected:
            return "\n".join(selected)
        else:
            msg = "'TYPE' column is required but the output doesn't have it: "
            raise tempest.lib.exceptions.TempestException(msg + output)

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

    def get_mac_address(self, nic=""):
        show_nic = "show {nic} ".format(nic=nic) if nic else ""
        cmd = "ip addr %s| awk '/ether/ {print $2}'" % show_nic
        return self.exec_command(cmd).strip().lower()

    def get_nic_name_by_mac(self, address):
        cmd = "ip -o link | awk '/%s/ {print $2}'" % address
        nic = self.exec_command(cmd)
        return nic.strip().strip(":").split('@')[0].lower()

    def get_nic_name_by_ip(self, address):
        cmd = "ip -o addr | awk '/%s/ {print $2}'" % address
        nic = self.exec_command(cmd)
        LOG.debug('(get_nic_name_by_ip) Command result: %s', nic)
        return nic.strip().strip(":").split('@')[0].lower()

    def get_dns_servers(self):
        cmd = 'cat /etc/resolv.conf'
        resolve_file = self.exec_command(cmd).strip().split('\n')
        entries = (l.split() for l in resolve_file)
        dns_servers = [l[1] for l in entries
                       if len(l) and l[0] == 'nameserver']
        return dns_servers

    def _renew_lease_udhcpc(self, fixed_ip=None):
        """Renews DHCP lease via udhcpc client. """
        file_path = '/var/run/udhcpc.'
        nic_name = self.get_nic_name_by_ip(fixed_ip)
        pid = self.exec_command('cat {path}{nic}.pid'.
                                format(path=file_path, nic=nic_name))
        pid = pid.strip()
        cmd = 'sudo /bin/kill -{sig} {pid}'.format(pid=pid, sig='USR1')
        self.exec_command(cmd)

    def _renew_lease_dhclient(self, fixed_ip=None):
        """Renews DHCP lease via dhclient client. """
        cmd = "sudo /sbin/dhclient -r && sudo /sbin/dhclient"
        self.exec_command(cmd)

    def renew_lease(self, fixed_ip=None, dhcp_client='udhcpc'):
        """Wrapper method for renewing DHCP lease via given client

        Supporting:
        * udhcpc
        * dhclient
        """
        # TODO(yfried): add support for dhcpcd
        supported_clients = ['udhcpc', 'dhclient']
        if dhcp_client not in supported_clients:
            raise tempest.lib.exceptions.InvalidConfiguration(
                '%s DHCP client unsupported' % dhcp_client)
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
            LOG.info("Contents of /dev: %s", self.exec_command(cmd_why))
            raise

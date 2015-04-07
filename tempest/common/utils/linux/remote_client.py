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
import time

import six

from tempest.common import ssh
from tempest import config
from tempest import exceptions

CONF = config.CONF


class RemoteClient(object):

    # NOTE(afazekas): It should always get an address instead of server
    def __init__(self, server, username, password=None, pkey=None):
        ssh_timeout = CONF.compute.ssh_timeout
        network = CONF.compute.network_for_ssh
        ip_version = CONF.compute.ip_version_for_ssh
        ssh_channel_timeout = CONF.compute.ssh_channel_timeout
        if isinstance(server, six.string_types):
            ip_address = server
        else:
            addresses = server['addresses'][network]
            for address in addresses:
                if address['version'] == ip_version:
                    ip_address = address['addr']
                    break
            else:
                raise exceptions.ServerUnreachable()
        self.ssh_client = ssh.Client(ip_address, username, password,
                                     ssh_timeout, pkey=pkey,
                                     channel_timeout=ssh_channel_timeout)

    def exec_command(self, cmd):
        return self.ssh_client.exec_command(cmd)

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
        command = 'cat /proc/cpuinfo | grep processor | wc -l'
        output = self.exec_command(command)
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

    def ping_host(self, host, count=CONF.compute.ping_count,
                  size=CONF.compute.ping_size):
        addr = netaddr.IPAddress(host)
        cmd = 'ping6' if addr.version == 6 else 'ping'
        cmd += ' -c{0} -w{0} -s{1} {2}'.format(count, size, host)
        return self.exec_command(cmd)

    def get_mac_address(self):
        cmd = "/bin/ip addr | awk '/ether/ {print $2}'"
        return self.exec_command(cmd)

    def get_nic_name(self, address):
        cmd = "/bin/ip -o addr | awk '/%s/ {print $2}'" % address
        return self.exec_command(cmd)

    def get_ip_list(self):
        cmd = "/bin/ip address"
        return self.exec_command(cmd)

    def assign_static_ip(self, nic, addr):
        cmd = "sudo /bin/ip addr add {ip}/{mask} dev {nic}".format(
            ip=addr, mask=CONF.network.tenant_network_mask_bits,
            nic=nic
        )
        return self.exec_command(cmd)

    def turn_nic_on(self, nic):
        cmd = "sudo /bin/ip link set {nic} up".format(nic=nic)
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
        nic_name = self.get_nic_name(fixed_ip)
        nic_name = nic_name.strip().lower()
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
        suported_clients = ['udhcpc', 'dhclient']
        dhcp_client = CONF.scenario.dhcp_client
        if dhcp_client not in suported_clients:
            raise exceptions.InvalidConfiguration('%s DHCP client unsupported'
                                                  % dhcp_client)
        if dhcp_client == 'udhcpc' and not fixed_ip:
            raise ValueError("need to set 'fixed_ip' for udhcpc client")
        return getattr(self, '_renew_lease_' + dhcp_client)(fixed_ip=fixed_ip)

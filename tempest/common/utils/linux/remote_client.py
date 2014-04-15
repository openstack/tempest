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
import six
import time

from tempest.common import ssh
from tempest import config
from tempest import exceptions

CONF = config.CONF


class RemoteClient():

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

    def get_files(self, path):
        # Return a list of comma separated files
        command = "ls -m " + path
        return self.exec_command(command).rstrip('\n').split(', ')

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

    def ping_host(self, host):
        cmd = 'ping -c1 -w1 %s' % host
        return self.exec_command(cmd)

    def get_mac_address(self):
        cmd = "/sbin/ifconfig | awk '/HWaddr/ {print $5}'"
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

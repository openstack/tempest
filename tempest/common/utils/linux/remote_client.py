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

from oslo_log import log as logging
import six
from tempest_lib.common import ssh

from tempest import config
from tempest import exceptions

CONF = config.CONF

LOG = logging.getLogger(__name__)


class RemoteClient(object):

    # NOTE(afazekas): It should always get an address instead of server
    def __init__(self, server, username, password=None, pkey=None):
        ssh_timeout = CONF.validation.ssh_timeout
        network = CONF.compute.network_for_ssh
        ip_version = CONF.validation.ip_version_for_ssh
        connect_timeout = CONF.validation.connect_timeout
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
                                     channel_timeout=connect_timeout)

    def exec_command(self, cmd):
        # Shell options below add more clearness on failures,
        # path is extended for some non-cirros guest oses (centos7)
        cmd = CONF.compute.ssh_shell_prologue + " " + cmd
        LOG.debug("Remote command: %s" % cmd)
        return self.ssh_client.exec_command(cmd)

    def get_kernel_modules(self):
        """
        :return: A list of kernel modules currently loaded
        """
        kernel_modules = []
        lsmod_output = self.exec_command('/sbin/lsmod')
        module_signature_re = re.compile(r"""^(\w+)\s+(\d+).*""",
                                         re.VERBOSE | re.IGNORECASE)
        for module_data in lsmod_output.splitlines():
            module = module_signature_re.match(module_data)
            if module:
                kernel_modules.append(module.group(1))

        return kernel_modules

    def is_dot1q_enabled(self):
        """
        Determines if the VM has support for 802.1q in the kernel.
        :return: Boolean -  True indicates the VM is capable of 802.1q
                            False otherwise
        """
        return '8021q' in self.get_kernel_modules()

    def load_dot1q(self):
        """
        Tries to load kernel module for 802.1q
        :return: True if 802.1Q is loaded False otherwise
        """
        self.exec_command('sudo /sbin/modprobe 8021q')
        return self.is_dot1q_enabled()

    def config_dot1q(self, vlan_id, ip_address, parent_interface='eth0'):
        """
        Configure a VLAN interface on the VM
        :param vlan_id:  The VLAN number
        :param ip_address: in the form of 192.168.1.1/24
        :param parent_interface: The interface to base the VLAN interface on
        """
        if not self.is_dot1q_enabled():
            self.load_dot1q()

        if not self.is_dot1q_enabled():
            msg = "Virtual machine image needs to support 8021q in the kernel"
            raise exceptions.InvalidConfiguration(msg)

        # Check address format
        ip_re = re.compile(r"""
                            ^(\d{1,3}\.
                            \d{1,3}\.
                            \d{1,3}\.
                            \d{1,3})
                            /(\d{1,2})$
                            """, re.VERBOSE | re.IGNORECASE)
        if not ip_re.match(ip_address):
            msg = "Invalid IP address given {0}".format(ip_address)
            raise exceptions.InvalidConfiguration(msg)

        link_cmd = "sudo /bin/ip link "
        ip_cmd = "sudo /bin/ip "
        dev = "{0}.{1}".format(parent_interface, vlan_id)
        self.exec_command("{0} add link {1} name {2} type vlan id {3}".format(
            link_cmd,
            parent_interface,
            dev,
            vlan_id))
        self.exec_command("{0} ".format(link_cmd))
        self.exec_command("{0} addr add {1} dev {2}".format(ip_cmd,
                                                            ip_address,
                                                            dev))
        self.exec_command("{0} set dev {1} up".format(link_cmd, dev))
        return self.exec_command("sudo /bin/ip -d link show {0}".format(dev))

    def interface_stats(self, interface='eth0'):
        """
        :param interface:  The interface to get stats
        :return: A dictionary containing the interface stats
        """
        raw_data = self.exec_command("sudo /bin/ip -s link")

        # The inital data structure
        istats = {'interface':          interface,
                  'hwaddr':             None,
                  'mtu':                None,
                  'rx':     {'pkts':    None,
                             'errors':  None,
                             'dropped': None,
                             'bytes':   None},
                  'tx':     {'pkts':    None,
                             'errors':  None,
                             'dropped': None,
                             'bytes':   None}
                  }

        intf_re = re.compile(r"\s+link/ether\s+([0-9a-f:]+).*")

        mtu_re = re.compile(r"^(\d+)[:]\s+" + interface +
                            ".*[:].+[>]\s+mtu\s+(\d+).*")

        counters_re = re.compile("^\s+(\d+)"
                                 "\s+(\d+)"
                                 "\s+(\d+)"
                                 "\s+(\d+)"
                                 "\s+(\d+)"
                                 "\s+(\d+).*", re.VERBOSE)

        interface_context = False
        dir = 'rx'
        for line in raw_data.splitlines():

            mtu_match = mtu_re.match(line)
            if mtu_match:
                istats['mtu'] = mtu_match.group(2)
                interface_context = True
                continue

            intf_match = intf_re.match(line)
            if interface_context and intf_match:
                istats['hwaddr'] = intf_match.group(1)
                continue

            counters = counters_re.match(line)
            if interface_context and counters:
                istats[dir]['bytes'] = int(counters.group(1))
                istats[dir]['pkts'] = int(counters.group(2))
                istats[dir]['errors'] = int(counters.group(3))
                istats[dir]['dropped'] = int(counters.group(4))
                if dir == 'tx':
                    break
                dir = 'tx'

        return istats

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
        output = self.exec_command('grep -c processor /proc/cpuinfo')
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
                  size=CONF.compute.ping_size, interface=None, interval=None):
        addr = netaddr.IPAddress(host)
        cmd = 'ping6' if addr.version == 6 else 'ping'
        if interface:
            cmd += ' -I{0} '.format(interface)

        if interval:
            cmd += ' -i{0} '.format(interval)

        cmd += ' -c{0} -w{0} -s{1} {2}'.format(count, size, host)
        return self.exec_command(cmd)

    def get_mac_address(self):
        cmd = "ip addr | awk '/ether/ {print $2}'"
        return self.exec_command(cmd)

    def get_nic_name(self, address):
        cmd = "ip -o addr | awk '/%s/ {print $2}'" % address
        return self.exec_command(cmd)

    def get_ip_list(self):
        cmd = "ip address"
        return self.exec_command(cmd)

    def assign_static_ip(self, nic, addr):
        cmd = "sudo ip addr add {ip}/{mask} dev {nic}".format(
            ip=addr, mask=CONF.network.tenant_network_mask_bits,
            nic=nic
        )
        return self.exec_command(cmd)

    def turn_nic_on(self, nic):
        cmd = "sudo ip link set {nic} up".format(nic=nic)
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

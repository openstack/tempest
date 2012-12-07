import re
import time

from tempest.common.ssh import Client
from tempest.common import utils
from tempest.config import TempestConfig
from tempest.exceptions import ServerUnreachable
from tempest.exceptions import SSHTimeout


class RemoteClient():

    #Note(afazekas): It should always get an address instead of server
    def __init__(self, server, username, password=None, pkey=None):
        ssh_timeout = TempestConfig().compute.ssh_timeout
        network = TempestConfig().compute.network_for_ssh
        ip_version = TempestConfig().compute.ip_version_for_ssh
        if isinstance(server, basestring):
            ip_address = server
        else:
            addresses = server['addresses'][network]
            for address in addresses:
                if address['version'] == ip_version:
                    ip_address = address['addr']
                    break
            else:
                raise ServerUnreachable()

        self.ssh_client = Client(ip_address, username, password, ssh_timeout,
                                 pkey=pkey)
        if not self.ssh_client.test_connection_auth():
            raise SSHTimeout()

    def can_authenticate(self):
        # Re-authenticate
        return self.ssh_client.test_connection_auth()

    def hostname_equals_servername(self, expected_hostname):
        # Get hostname using command "hostname"
        actual_hostname = self.ssh_client.exec_command("hostname").rstrip()
        return expected_hostname == actual_hostname

    def get_files(self, path):
        # Return a list of comma seperated files
        command = "ls -m " + path
        return self.ssh_client.exec_command(command).rstrip('\n').split(', ')

    def get_ram_size_in_mb(self):
        output = self.ssh_client.exec_command('free -m | grep Mem')
        if output:
            return output.split()[1]

    def get_number_of_vcpus(self):
        command = 'cat /proc/cpuinfo | grep processor | wc -l'
        output = self.ssh_client.exec_command(command)
        return int(output)

    def get_partitions(self):
        # Return the contents of /proc/partitions
        command = 'cat /proc/partitions'
        output = self.ssh_client.exec_command(command)
        return output

    def get_boot_time(self):
        cmd = 'date -d "`cut -f1 -d. /proc/uptime` seconds ago" \
            "+%Y-%m-%d %H:%M:%S"'
        boot_time_string = self.ssh_client.exec_command(cmd)
        boot_time_string = boot_time_string.replace('\n', '')
        return time.strptime(boot_time_string, utils.LAST_REBOOT_TIME_FORMAT)

    def write_to_console(self, message):
        message = re.sub("([$\\`])", "\\\\\\\\\\1", message)
        # usually to /dev/ttyS0
        cmd = 'sudo sh -c "echo \\"%s\\" >/dev/console"' % message
        return self.ssh_client.exec_command(cmd)

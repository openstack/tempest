#    Licensed under the Apache License, Version 2.0 (the "License");
#    you may not use this file except in compliance with the License.
#    You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS,
#    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    See the License for the specific language governing permissions and
#    limitations under the License.

import socket
import subprocess

from tempest.common.utils import data_utils
from tempest.common import waiters
from tempest import config
from tempest.lib.common.utils import test_utils
import tempest.stress.stressaction as stressaction

CONF = config.CONF


class FloatingStress(stressaction.StressAction):

    # from the scenario manager
    def ping_ip_address(self, ip_address):
        cmd = ['ping', '-c1', '-w1', ip_address]

        proc = subprocess.Popen(cmd,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE)
        proc.communicate()
        success = proc.returncode == 0
        return success

    def tcp_connect_scan(self, addr, port):
        # like tcp
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            s.connect((addr, port))
        except socket.error as exc:
            self.logger.info("%s(%s): %s", self.server_id, self.floating['ip'],
                             str(exc))
            return False
        self.logger.info("%s(%s): Connected :)", self.server_id,
                         self.floating['ip'])
        s.close()
        return True

    def check_port_ssh(self):
        def func():
            return self.tcp_connect_scan(self.floating['ip'], 22)
        if not test_utils.call_until_true(func, self.check_timeout,
                                          self.check_interval):
            raise RuntimeError("Cannot connect to the ssh port.")

    def check_icmp_echo(self):
        self.logger.info("%s(%s): Pinging..",
                         self.server_id, self.floating['ip'])

        def func():
            return self.ping_ip_address(self.floating['ip'])
        if not test_utils.call_until_true(func, self.check_timeout,
                                          self.check_interval):
            raise RuntimeError("%s(%s): Cannot ping the machine.",
                               self.server_id, self.floating['ip'])
        self.logger.info("%s(%s): pong :)",
                         self.server_id, self.floating['ip'])

    def _create_vm(self):
        self.name = name = data_utils.rand_name(
            self.__class__.__name__ + "-instance")
        servers_client = self.manager.servers_client
        self.logger.info("creating %s" % name)
        vm_args = self.vm_extra_args.copy()
        vm_args['security_groups'] = [self.sec_grp]
        server = servers_client.create_server(name=name, imageRef=self.image,
                                              flavorRef=self.flavor,
                                              **vm_args)['server']
        self.server_id = server['id']
        if self.wait_after_vm_create:
            waiters.wait_for_server_status(self.manager.servers_client,
                                           self.server_id, 'ACTIVE')

    def _destroy_vm(self):
        self.logger.info("deleting %s" % self.server_id)
        self.manager.servers_client.delete_server(self.server_id)
        waiters.wait_for_server_termination(self.manager.servers_client,
                                            self.server_id)
        self.logger.info("deleted %s" % self.server_id)

    def _create_sec_group(self):
        sec_grp_cli = self.manager.compute_security_groups_client
        s_name = data_utils.rand_name(self.__class__.__name__ + '-sec_grp')
        s_description = data_utils.rand_name('desc')
        self.sec_grp = sec_grp_cli.create_security_group(
            name=s_name, description=s_description)['security_group']
        create_rule = sec_grp_cli.create_security_group_rule
        create_rule(parent_group_id=self.sec_grp['id'], ip_protocol='tcp',
                    from_port=22, to_port=22)
        create_rule(parent_group_id=self.sec_grp['id'], ip_protocol='icmp',
                    from_port=-1, to_port=-1)

    def _destroy_sec_grp(self):
        sec_grp_cli = self.manager.compute_security_groups_client
        sec_grp_cli.delete_security_group(self.sec_grp['id'])

    def _create_floating_ip(self):
        floating_cli = self.manager.compute_floating_ips_client
        self.floating = (floating_cli.create_floating_ip(self.floating_pool)
                         ['floating_ip'])

    def _destroy_floating_ip(self):
        cli = self.manager.compute_floating_ips_client
        cli.delete_floating_ip(self.floating['id'])
        cli.wait_for_resource_deletion(self.floating['id'])
        self.logger.info("Deleted Floating IP %s", str(self.floating['ip']))

    def setUp(self, **kwargs):
        self.image = CONF.compute.image_ref
        self.flavor = CONF.compute.flavor_ref
        self.vm_extra_args = kwargs.get('vm_extra_args', {})
        self.wait_after_vm_create = kwargs.get('wait_after_vm_create',
                                               True)
        self.new_vm = kwargs.get('new_vm', False)
        self.new_sec_grp = kwargs.get('new_sec_group', False)
        self.new_floating = kwargs.get('new_floating', False)
        self.reboot = kwargs.get('reboot', False)
        self.floating_pool = kwargs.get('floating_pool', None)
        self.verify = kwargs.get('verify', ('check_port_ssh',
                                            'check_icmp_echo'))
        self.check_timeout = kwargs.get('check_timeout', 120)
        self.check_interval = kwargs.get('check_interval', 1)
        self.wait_for_disassociate = kwargs.get('wait_for_disassociate',
                                                True)

        # allocate floating
        if not self.new_floating:
            self._create_floating_ip()
        # add security group
        if not self.new_sec_grp:
            self._create_sec_group()
        # create vm
        if not self.new_vm:
            self._create_vm()

    def wait_disassociate(self):
        cli = self.manager.compute_floating_ips_client

        def func():
            floating = (cli.show_floating_ip(self.floating['id'])
                        ['floating_ip'])
            return floating['instance_id'] is None

        if not test_utils.call_until_true(func, self.check_timeout,
                                          self.check_interval):
            raise RuntimeError("IP disassociate timeout!")

    def run_core(self):
        cli = self.manager.compute_floating_ips_client
        cli.associate_floating_ip_to_server(self.floating['ip'],
                                            self.server_id)
        for method in self.verify:
            m = getattr(self, method)
            m()
        cli.disassociate_floating_ip_from_server(self.floating['ip'],
                                                 self.server_id)
        if self.wait_for_disassociate:
            self.wait_disassociate()

    def run(self):
        if self.new_sec_grp:
            self._create_sec_group()
        if self.new_floating:
            self._create_floating_ip()
        if self.new_vm:
            self._create_vm()
        if self.reboot:
            self.manager.servers_client.reboot(self.server_id, 'HARD')
            waiters.wait_for_server_status(self.manager.servers_client,
                                           self.server_id, 'ACTIVE')

        self.run_core()

        if self.new_vm:
            self._destroy_vm()
        if self.new_floating:
            self._destroy_floating_ip()
        if self.new_sec_grp:
            self._destroy_sec_grp()

    def tearDown(self):
        if not self.new_vm:
            self._destroy_vm()
        if not self.new_floating:
            self._destroy_floating_ip()
        if not self.new_sec_grp:
            self._destroy_sec_grp()

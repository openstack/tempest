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

import re

from tempest.common.utils import data_utils
from tempest.common.utils.linux import remote_client
from tempest.common import waiters
from tempest import config
from tempest.lib.common.utils import test_utils
import tempest.stress.stressaction as stressaction

CONF = config.CONF


class VolumeVerifyStress(stressaction.StressAction):

    def _create_keypair(self):
        keyname = data_utils.rand_name("key")
        self.key = (self.manager.keypairs_client.create_keypair(name=keyname)
                    ['keypair'])

    def _delete_keypair(self):
        self.manager.keypairs_client.delete_keypair(self.key['name'])

    def _create_vm(self):
        self.name = name = data_utils.rand_name(
            self.__class__.__name__ + "-instance")
        servers_client = self.manager.servers_client
        self.logger.info("creating %s" % name)
        vm_args = self.vm_extra_args.copy()
        vm_args['security_groups'] = [self.sec_grp]
        vm_args['key_name'] = self.key['name']
        server = servers_client.create_server(name=name, imageRef=self.image,
                                              flavorRef=self.flavor,
                                              **vm_args)['server']
        self.server_id = server['id']
        waiters.wait_for_server_status(self.manager.servers_client,
                                       self.server_id, 'ACTIVE')

    def _destroy_vm(self):
        self.logger.info("deleting server: %s" % self.server_id)
        self.manager.servers_client.delete_server(self.server_id)
        waiters.wait_for_server_termination(self.manager.servers_client,
                                            self.server_id)
        self.logger.info("deleted server: %s" % self.server_id)

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

    def _create_volume(self):
        name = data_utils.rand_name(self.__class__.__name__ + "-volume")
        self.logger.info("creating volume: %s" % name)
        volumes_client = self.manager.volumes_client
        self.volume = volumes_client.create_volume(
            display_name=name, size=CONF.volume.volume_size)['volume']
        volumes_client.wait_for_volume_status(self.volume['id'],
                                              'available')
        self.logger.info("created volume: %s" % self.volume['id'])

    def _delete_volume(self):
        self.logger.info("deleting volume: %s" % self.volume['id'])
        volumes_client = self.manager.volumes_client
        volumes_client.delete_volume(self.volume['id'])
        volumes_client.wait_for_resource_deletion(self.volume['id'])
        self.logger.info("deleted volume: %s" % self.volume['id'])

    def _wait_disassociate(self):
        cli = self.manager.compute_floating_ips_client

        def func():
            floating = (cli.show_floating_ip(self.floating['id'])
                        ['floating_ip'])
            return floating['instance_id'] is None

        if not test_utils.call_until_true(func, CONF.compute.build_timeout,
                                          CONF.compute.build_interval):
            raise RuntimeError("IP disassociate timeout!")

    def new_server_ops(self):
        self._create_vm()
        cli = self.manager.compute_floating_ips_client
        cli.associate_floating_ip_to_server(self.floating['ip'],
                                            self.server_id)
        if self.ssh_test_before_attach and self.enable_ssh_verify:
            self.logger.info("Scanning for block devices via ssh on %s"
                             % self.server_id)
            self.part_wait(self.detach_match_count)

    def setUp(self, **kwargs):
        """Note able configuration combinations:

            Closest options to the test_stamp_pattern:
                new_server = True
                new_volume = True
                enable_ssh_verify = True
                ssh_test_before_attach = False
            Just attaching:
                new_server = False
                new_volume = False
                enable_ssh_verify = True
                ssh_test_before_attach = True
            Mostly API load by repeated attachment:
                new_server = False
                new_volume = False
                enable_ssh_verify = False
                ssh_test_before_attach = False
            Minimal Nova load, but cinder load not decreased:
                new_server = False
                new_volume = True
                enable_ssh_verify = True
                ssh_test_before_attach = True
        """
        self.image = CONF.compute.image_ref
        self.flavor = CONF.compute.flavor_ref
        self.vm_extra_args = kwargs.get('vm_extra_args', {})
        self.floating_pool = kwargs.get('floating_pool', None)
        self.new_volume = kwargs.get('new_volume', True)
        self.new_server = kwargs.get('new_server', False)
        self.enable_ssh_verify = kwargs.get('enable_ssh_verify', True)
        self.ssh_test_before_attach = kwargs.get('ssh_test_before_attach',
                                                 False)
        self.part_line_re = re.compile(kwargs.get('part_line_re', '.*vd.*'))
        self.detach_match_count = kwargs.get('detach_match_count', 1)
        self.attach_match_count = kwargs.get('attach_match_count', 2)
        self.part_name = kwargs.get('part_name', '/dev/vdc')

        self._create_floating_ip()
        self._create_sec_group()
        self._create_keypair()
        private_key = self.key['private_key']
        username = CONF.validation.image_ssh_user
        self.remote_client = remote_client.RemoteClient(self.floating['ip'],
                                                        username,
                                                        pkey=private_key)
        if not self.new_volume:
            self._create_volume()
        if not self.new_server:
            self.new_server_ops()

    # now we just test that the number of partitions has increased or decreased
    def part_wait(self, num_match):
        def _part_state():
            self.partitions = self.remote_client.get_partitions().split('\n')
            matching = 0
            for part_line in self.partitions[1:]:
                if self.part_line_re.match(part_line):
                    matching += 1
            return matching == num_match
        if test_utils.call_until_true(_part_state,
                                      CONF.compute.build_timeout,
                                      CONF.compute.build_interval):
            return
        else:
            raise RuntimeError("Unexpected partitions: %s",
                               str(self.partitions))

    def run(self):
        if self.new_server:
            self.new_server_ops()
        if self.new_volume:
            self._create_volume()
        servers_client = self.manager.servers_client
        self.logger.info("attach volume (%s) to vm %s" %
                         (self.volume['id'], self.server_id))
        servers_client.attach_volume(self.server_id,
                                     volumeId=self.volume['id'],
                                     device=self.part_name)
        self.manager.volumes_client.wait_for_volume_status(self.volume['id'],
                                                           'in-use')
        if self.enable_ssh_verify:
            self.logger.info("Scanning for new block device on %s"
                             % self.server_id)
            self.part_wait(self.attach_match_count)

        servers_client.detach_volume(self.server_id,
                                     self.volume['id'])
        self.manager.volumes_client.wait_for_volume_status(self.volume['id'],
                                                           'available')
        if self.enable_ssh_verify:
            self.logger.info("Scanning for block device disappearance on %s"
                             % self.server_id)
            self.part_wait(self.detach_match_count)
        if self.new_volume:
            self._delete_volume()
        if self.new_server:
            self._destroy_vm()

    def tearDown(self):
        cli = self.manager.compute_floating_ips_client
        cli.disassociate_floating_ip_from_server(self.floating['ip'],
                                                 self.server_id)
        self._wait_disassociate()
        if not self.new_server:
            self._destroy_vm()
        self._delete_keypair()
        self._destroy_floating_ip()
        self._destroy_sec_grp()
        if not self.new_volume:
            self._delete_volume()

# Copyright 2014 Scality
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

from oslo_log import log
import testtools

from tempest import config
from tempest.scenario import manager
from tempest import test

CONF = config.CONF

LOG = log.getLogger(__name__)


class TestShelveInstance(manager.ScenarioTest):
    """
    This test shelves then unshelves a Nova instance
    The following is the scenario outline:
     * boot a instance and create a timestamp file in it
     * shelve the instance
     * unshelve the instance
     * check the existence of the timestamp file in the unshelved instance

    """

    def _write_timestamp(self, server_or_ip):
        ssh_client = self.get_remote_client(server_or_ip)
        ssh_client.exec_command('date > /tmp/timestamp; sync')
        self.timestamp = ssh_client.exec_command('cat /tmp/timestamp')

    def _check_timestamp(self, server_or_ip):
        ssh_client = self.get_remote_client(server_or_ip)
        got_timestamp = ssh_client.exec_command('cat /tmp/timestamp')
        self.assertEqual(self.timestamp, got_timestamp)

    def _shelve_then_unshelve_server(self, server):
        self.servers_client.shelve_server(server['id'])
        offload_time = CONF.compute.shelved_offload_time
        if offload_time >= 0:
            self.servers_client.wait_for_server_status(
                server['id'], 'SHELVED_OFFLOADED', extra_timeout=offload_time)
        else:
            self.servers_client.wait_for_server_status(server['id'], 'SHELVED')
            self.servers_client.shelve_offload_server(server['id'])
            self.servers_client.wait_for_server_status(server['id'],
                                                       'SHELVED_OFFLOADED')
        self.servers_client.unshelve_server(server['id'])
        self.servers_client.wait_for_server_status(server['id'], 'ACTIVE')

    @test.idempotent_id('1164e700-0af0-4a4c-8792-35909a88743c')
    @testtools.skipUnless(CONF.compute_feature_enabled.shelve,
                          'Shelve is not available.')
    @test.services('compute', 'network', 'image')
    def test_shelve_instance(self):
        self.keypair = self.create_keypair()

        self.security_group = self._create_security_group()
        security_groups = [{'name': self.security_group['name']}]

        create_kwargs = {
            'key_name': self.keypair['name'],
            'security_groups': security_groups
        }
        server = self.create_server(image=CONF.compute.image_ref,
                                    create_kwargs=create_kwargs)

        if CONF.compute.use_floatingip_for_ssh:
            floating_ip = self.floating_ips_client.create_floating_ip()
            self.addCleanup(self.delete_wrapper,
                            self.floating_ips_client.delete_floating_ip,
                            floating_ip['id'])
            self.floating_ips_client.associate_floating_ip_to_server(
                floating_ip['ip'], server['id'])
            self._write_timestamp(floating_ip['ip'])
        else:
            self._write_timestamp(server)

        # Prevent bug #1257594 from coming back
        # Unshelve used to boot the instance with the original image, not
        # with the instance snapshot
        self._shelve_then_unshelve_server(server)
        if CONF.compute.use_floatingip_for_ssh:
            self._check_timestamp(floating_ip['ip'])
        else:
            self._check_timestamp(server)

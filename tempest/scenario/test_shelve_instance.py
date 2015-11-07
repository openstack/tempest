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

from tempest.common import waiters
from tempest import config
from tempest.scenario import manager
from tempest import test

CONF = config.CONF

LOG = log.getLogger(__name__)


class TestShelveInstance(manager.ScenarioTest):
    """
    This test shelves then unshelves a Nova instance
    The following is the scenario outline:
     * boot an instance and create a timestamp file in it
     * shelve the instance
     * unshelve the instance
     * check the existence of the timestamp file in the unshelved instance

    """

    def _shelve_then_unshelve_server(self, server):
        self.servers_client.shelve_server(server['id'])
        offload_time = CONF.compute.shelved_offload_time
        if offload_time >= 0:
            waiters.wait_for_server_status(self.servers_client, server['id'],
                                           'SHELVED_OFFLOADED',
                                           extra_timeout=offload_time)
        else:
            waiters.wait_for_server_status(self.servers_client,
                                           server['id'], 'SHELVED')
            self.servers_client.shelve_offload_server(server['id'])
            waiters.wait_for_server_status(self.servers_client, server['id'],
                                           'SHELVED_OFFLOADED')
        self.servers_client.unshelve_server(server['id'])
        waiters.wait_for_server_status(self.servers_client, server['id'],
                                       'ACTIVE')

    def _create_server_then_shelve_and_unshelve(self, boot_from_volume=False):
        keypair = self.create_keypair()

        security_group = self._create_security_group()
        security_groups = [{'name': security_group['name']}]
        create_kwargs = {
            'key_name': keypair['name'],
            'security_groups': security_groups
        }

        if boot_from_volume:
            volume = self.create_volume(size=CONF.volume.volume_size,
                                        imageRef=CONF.compute.image_ref)
            bd_map = [{
                'device_name': 'vda',
                'volume_id': volume['id'],
                'delete_on_termination': '0'}]

            create_kwargs['block_device_mapping'] = bd_map
            server = self.create_server(create_kwargs=create_kwargs)
        else:
            server = self.create_server(image=CONF.compute.image_ref,
                                        create_kwargs=create_kwargs)

        if CONF.compute.use_floatingip_for_ssh:
            floating_ip = self.create_floating_ip(server)['ip']
            timestamp = self.create_timestamp(
                floating_ip, private_key=keypair['private_key'])
        else:
            timestamp = self.create_timestamp(
                server, private_key=keypair['private_key'])

        # Prevent bug #1257594 from coming back
        # Unshelve used to boot the instance with the original image, not
        # with the instance snapshot
        self._shelve_then_unshelve_server(server)
        if CONF.compute.use_floatingip_for_ssh:
            timestamp2 = self.get_timestamp(floating_ip,
                                            private_key=keypair['private_key'])
        else:
            timestamp2 = self.get_timestamp(server,
                                            private_key=keypair['private_key'])
        self.assertEqual(timestamp, timestamp2)

    @test.idempotent_id('1164e700-0af0-4a4c-8792-35909a88743c')
    @testtools.skipUnless(CONF.compute_feature_enabled.shelve,
                          'Shelve is not available.')
    @test.services('compute', 'network', 'image')
    def test_shelve_instance(self):
        self._create_server_then_shelve_and_unshelve()

    @test.idempotent_id('c1b6318c-b9da-490b-9c67-9339b627271f')
    @testtools.skipUnless(CONF.compute_feature_enabled.shelve,
                          'Shelve is not available.')
    @test.services('compute', 'volume', 'network', 'image')
    def test_shelve_volume_backed_instance(self):
        self._create_server_then_shelve_and_unshelve(boot_from_volume=True)

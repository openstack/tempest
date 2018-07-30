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

import testtools

from tempest.common import compute
from tempest.common import utils
from tempest.common import waiters
from tempest import config
from tempest.lib import decorators
from tempest.scenario import manager

CONF = config.CONF


class TestShelveInstance(manager.ScenarioTest):
    """This test shelves then unshelves a Nova instance

    The following is the scenario outline:
     * boot an instance and create a timestamp file in it
     * shelve the instance
     * unshelve the instance
     * check the existence of the timestamp file in the unshelved instance

    """

    @classmethod
    def skip_checks(cls):
        super(TestShelveInstance, cls).skip_checks()
        if not CONF.compute_feature_enabled.shelve:
            raise cls.skipException("Shelve is not available.")

    def _shelve_then_unshelve_server(self, server):
        compute.shelve_server(self.servers_client, server['id'],
                              force_shelve_offload=True)

        self.servers_client.unshelve_server(server['id'])
        waiters.wait_for_server_status(self.servers_client, server['id'],
                                       'ACTIVE')

    def _create_server_then_shelve_and_unshelve(self, boot_from_volume=False):
        keypair = self.create_keypair()

        security_group = self._create_security_group()
        security_groups = [{'name': security_group['name']}]

        server = self.create_server(
            key_name=keypair['name'],
            security_groups=security_groups,
            volume_backed=boot_from_volume)

        instance_ip = self.get_server_ip(server)
        timestamp = self.create_timestamp(instance_ip,
                                          private_key=keypair['private_key'],
                                          server=server)

        # Prevent bug #1257594 from coming back
        # Unshelve used to boot the instance with the original image, not
        # with the instance snapshot
        self._shelve_then_unshelve_server(server)

        timestamp2 = self.get_timestamp(instance_ip,
                                        private_key=keypair['private_key'],
                                        server=server)
        self.assertEqual(timestamp, timestamp2)

    @decorators.attr(type='slow')
    @decorators.idempotent_id('1164e700-0af0-4a4c-8792-35909a88743c')
    @testtools.skipUnless(CONF.network.public_network_id,
                          'The public_network_id option must be specified.')
    @utils.services('compute', 'network', 'image')
    def test_shelve_instance(self):
        self._create_server_then_shelve_and_unshelve()

    @decorators.attr(type='slow')
    @decorators.idempotent_id('c1b6318c-b9da-490b-9c67-9339b627271f')
    @testtools.skipUnless(CONF.network.public_network_id,
                          'The public_network_id option must be specified.')
    @utils.services('compute', 'volume', 'network', 'image')
    def test_shelve_volume_backed_instance(self):
        self._create_server_then_shelve_and_unshelve(boot_from_volume=True)

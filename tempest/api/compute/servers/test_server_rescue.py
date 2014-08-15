# Copyright 2013 Hewlett-Packard Development Company, L.P.
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

from tempest.api.compute import base
from tempest.common.utils import data_utils
from tempest import config
from tempest import test

CONF = config.CONF


class ServerRescueTestJSON(base.BaseV2ComputeTest):

    @classmethod
    @test.safe_setup
    def setUpClass(cls):
        if not CONF.compute_feature_enabled.rescue:
            msg = "Server rescue not available."
            raise cls.skipException(msg)

        cls.set_network_resources(network=True, subnet=True, router=True)
        super(ServerRescueTestJSON, cls).setUpClass()

        # Floating IP creation
        resp, body = cls.floating_ips_client.create_floating_ip()
        cls.floating_ip_id = str(body['id']).strip()
        cls.floating_ip = str(body['ip']).strip()

        # Security group creation
        cls.sg_name = data_utils.rand_name('sg')
        cls.sg_desc = data_utils.rand_name('sg-desc')
        resp, cls.sg = \
            cls.security_groups_client.create_security_group(cls.sg_name,
                                                             cls.sg_desc)
        cls.sg_id = cls.sg['id']

        # Create a volume and wait for it to become ready for attach
        resp, cls.volume = cls.volumes_extensions_client.create_volume(
            1, display_name=data_utils.rand_name(cls.__name__ + '_volume'))
        cls.volumes_extensions_client.wait_for_volume_status(
            cls.volume['id'], 'available')

        # Server for positive tests
        resp, server = cls.create_test_server(wait_until='BUILD')
        cls.server_id = server['id']
        cls.password = server['adminPass']
        cls.servers_client.wait_for_server_status(cls.server_id, 'ACTIVE')

    def setUp(self):
        super(ServerRescueTestJSON, self).setUp()

    @classmethod
    def tearDownClass(cls):
        # Deleting the floating IP which is created in this method
        cls.floating_ips_client.delete_floating_ip(cls.floating_ip_id)
        cls.delete_volume(cls.volume['id'])
        resp, cls.sg = cls.security_groups_client.delete_security_group(
            cls.sg_id)
        super(ServerRescueTestJSON, cls).tearDownClass()

    def tearDown(self):
        super(ServerRescueTestJSON, self).tearDown()

    def _unrescue(self, server_id):
        resp, body = self.servers_client.unrescue_server(server_id)
        self.assertEqual(202, resp.status)
        self.servers_client.wait_for_server_status(server_id, 'ACTIVE')

    @test.attr(type='smoke')
    def test_rescue_unrescue_instance(self):
        resp, body = self.servers_client.rescue_server(
            self.server_id, adminPass=self.password)
        self.assertEqual(200, resp.status)
        self.servers_client.wait_for_server_status(self.server_id, 'RESCUE')
        resp, body = self.servers_client.unrescue_server(self.server_id)
        self.assertEqual(202, resp.status)
        self.servers_client.wait_for_server_status(self.server_id, 'ACTIVE')

    @test.attr(type='gate')
    def test_rescued_vm_associate_dissociate_floating_ip(self):
        # Rescue the server
        self.servers_client.rescue_server(
            self.server_id, adminPass=self.password)
        self.servers_client.wait_for_server_status(self.server_id, 'RESCUE')
        self.addCleanup(self._unrescue, self.server_id)

        # Association of floating IP to a rescued vm
        client = self.floating_ips_client
        resp, body = client.associate_floating_ip_to_server(self.floating_ip,
                                                            self.server_id)
        self.assertEqual(202, resp.status)

        # Disassociation of floating IP that was associated in this method
        resp, body = \
            client.disassociate_floating_ip_from_server(self.floating_ip,
                                                        self.server_id)
        self.assertEqual(202, resp.status)

    @test.attr(type='gate')
    def test_rescued_vm_add_remove_security_group(self):
        # Rescue the server
        self.servers_client.rescue_server(
            self.server_id, adminPass=self.password)
        self.servers_client.wait_for_server_status(self.server_id, 'RESCUE')
        self.addCleanup(self._unrescue, self.server_id)

        # Add Security group
        resp, body = self.servers_client.add_security_group(self.server_id,
                                                            self.sg_name)
        self.assertEqual(202, resp.status)

        # Delete Security group
        resp, body = self.servers_client.remove_security_group(self.server_id,
                                                               self.sg_name)
        self.assertEqual(202, resp.status)


class ServerRescueTestXML(ServerRescueTestJSON):
    _interface = 'xml'

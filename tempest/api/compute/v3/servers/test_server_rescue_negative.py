# Copyright 2013 Hewlett-Packard Development Company, L.P.
# Copyright 2014 NEC Corporation.  All rights reserved.
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

from tempest.api.compute import base
from tempest.common.utils import data_utils
from tempest import config
from tempest import exceptions
from tempest import test

CONF = config.CONF


class ServerRescueNegativeV3Test(base.BaseV3ComputeTest):

    @classmethod
    @test.safe_setup
    def setUpClass(cls):
        if not CONF.compute_feature_enabled.rescue:
            msg = "Server rescue not available."
            raise cls.skipException(msg)

        super(ServerRescueNegativeV3Test, cls).setUpClass()
        cls.device = CONF.compute.volume_device_name

        # Create a volume and wait for it to become ready for attach
        resp, cls.volume = cls.volumes_client.create_volume(
            1, display_name=data_utils.rand_name(cls.__name__ + '_volume'))
        cls.volumes_client.wait_for_volume_status(
            cls.volume['id'], 'available')

        # Server for negative tests
        resp, server = cls.create_test_server(wait_until='BUILD')
        resp, resc_server = cls.create_test_server(wait_until='ACTIVE')
        cls.server_id = server['id']
        cls.password = server['admin_password']
        cls.rescue_id = resc_server['id']
        cls.rescue_password = resc_server['admin_password']

        cls.servers_client.rescue_server(
            cls.rescue_id, admin_password=cls.rescue_password)
        cls.servers_client.wait_for_server_status(cls.rescue_id, 'RESCUE')
        cls.servers_client.wait_for_server_status(cls.server_id, 'ACTIVE')

    @classmethod
    def tearDownClass(cls):
        if hasattr(cls, 'volume'):
            cls.delete_volume(cls.volume['id'])
        super(ServerRescueNegativeV3Test, cls).tearDownClass()

    def _detach(self, server_id, volume_id):
        self.servers_client.detach_volume(server_id, volume_id)
        self.volumes_client.wait_for_volume_status(volume_id,
                                                   'available')

    def _unrescue(self, server_id):
        resp, body = self.servers_client.unrescue_server(server_id)
        self.assertEqual(202, resp.status)
        self.servers_client.wait_for_server_status(server_id, 'ACTIVE')

    def _unpause(self, server_id):
        resp, body = self.servers_client.unpause_server(server_id)
        self.assertEqual(202, resp.status)
        self.servers_client.wait_for_server_status(server_id, 'ACTIVE')

    @testtools.skipUnless(CONF.compute_feature_enabled.pause,
                          'Pause is not available.')
    @test.attr(type=['negative', 'gate'])
    def test_rescue_paused_instance(self):
        # Rescue a paused server
        resp, body = self.servers_client.pause_server(
            self.server_id)
        self.addCleanup(self._unpause, self.server_id)
        self.assertEqual(202, resp.status)
        self.servers_client.wait_for_server_status(self.server_id, 'PAUSED')
        self.assertRaises(exceptions.Conflict,
                          self.servers_client.rescue_server,
                          self.server_id)

    @test.attr(type=['negative', 'gate'])
    def test_rescued_vm_reboot(self):
        self.assertRaises(exceptions.Conflict, self.servers_client.reboot,
                          self.rescue_id, 'HARD')

    @test.attr(type=['negative', 'gate'])
    def test_rescue_non_existent_server(self):
        # Rescue a non-existing server
        self.assertRaises(exceptions.NotFound,
                          self.servers_client.rescue_server,
                          data_utils.rand_uuid())

    @test.attr(type=['negative', 'gate'])
    def test_rescued_vm_rebuild(self):
        self.assertRaises(exceptions.Conflict,
                          self.servers_client.rebuild,
                          self.rescue_id,
                          self.image_ref_alt)

    @test.attr(type=['negative', 'gate'])
    def test_rescued_vm_attach_volume(self):
        # Rescue the server
        self.servers_client.rescue_server(self.server_id,
                                          admin_password=self.password)
        self.servers_client.wait_for_server_status(self.server_id, 'RESCUE')
        self.addCleanup(self._unrescue, self.server_id)

        # Attach the volume to the server
        self.assertRaises(exceptions.Conflict,
                          self.servers_client.attach_volume,
                          self.server_id,
                          self.volume['id'],
                          device='/dev/%s' % self.device)

    @test.attr(type=['negative', 'gate'])
    def test_rescued_vm_detach_volume(self):
        # Attach the volume to the server
        self.servers_client.attach_volume(self.server_id,
                                          self.volume['id'],
                                          device='/dev/%s' % self.device)
        self.volumes_client.wait_for_volume_status(self.volume['id'], 'in-use')

        # Rescue the server
        self.servers_client.rescue_server(self.server_id,
                                          admin_password=self.password)
        self.servers_client.wait_for_server_status(self.server_id, 'RESCUE')
        # addCleanup is a LIFO queue
        self.addCleanup(self._detach, self.server_id, self.volume['id'])
        self.addCleanup(self._unrescue, self.server_id)

        # Detach the volume from the server expecting failure
        self.assertRaises(exceptions.Conflict,
                          self.servers_client.detach_volume,
                          self.server_id,
                          self.volume['id'])

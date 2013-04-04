# vim: tabstop=4 shiftwidth=4 softtabstop=4

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

import testtools

from tempest.common.utils.data_utils import rand_name
import tempest.config
from tempest import exceptions
from tempest.test import attr
from tempest.tests.compute import base


class ServerRescueTestJSON(base.BaseComputeTest):
    _interface = 'json'

    run_ssh = tempest.config.TempestConfig().compute.run_ssh

    @classmethod
    def setUpClass(cls):
        super(ServerRescueTestJSON, cls).setUpClass()
        cls.device = 'vdf'

        #Floating IP creation
        resp, body = cls.floating_ips_client.create_floating_ip()
        cls.floating_ip_id = str(body['id']).strip()
        cls.floating_ip = str(body['ip']).strip()

        #Security group creation
        cls.sg_name = rand_name('sg')
        cls.sg_desc = rand_name('sg-desc')
        resp, cls.sg = \
        cls.security_groups_client.create_security_group(cls.sg_name,
                                                         cls.sg_desc)
        cls.sg_id = cls.sg['id']

        # Create a volume and wait for it to become ready for attach
        resp, cls.volume_to_attach = \
        cls.volumes_extensions_client.create_volume(1,
                                                    display_name=
                                                    'test_attach')
        cls.volumes_extensions_client.wait_for_volume_status(
                cls.volume_to_attach['id'], 'available')

        # Create a volume and wait for it to become ready for attach
        resp, cls.volume_to_detach = \
        cls.volumes_extensions_client.create_volume(1,
                                                    display_name=
                                                    'test_detach')
        cls.volumes_extensions_client.wait_for_volume_status(
                cls.volume_to_detach['id'], 'available')

        # Server for positive tests
        resp, server = cls.create_server(image_id=cls.image_ref,
                                         flavor=cls.flavor_ref,
                                         wait_until='BUILD')
        resp, resc_server = cls.create_server(image_id=cls.image_ref,
                                              flavor=cls.flavor_ref,
                                              wait_until='ACTIVE')
        cls.server_id = server['id']
        cls.password = server['adminPass']
        cls.servers_client.wait_for_server_status(cls.server_id, 'ACTIVE')

        # Server for negative tests
        cls.rescue_id = resc_server['id']
        cls.rescue_password = resc_server['adminPass']

        cls.servers_client.rescue_server(
            cls.rescue_id, cls.rescue_password)
        cls.servers_client.wait_for_server_status(cls.rescue_id, 'RESCUE')

    def setUp(self):
        super(ServerRescueTestJSON, self).setUp()

    @classmethod
    def tearDownClass(cls):
        super(ServerRescueTestJSON, cls).tearDownClass()
        #Deleting the floating IP which is created in this method
        cls.floating_ips_client.delete_floating_ip(cls.floating_ip_id)
        client = cls.volumes_extensions_client
        client.delete_volume(str(cls.volume_to_attach['id']).strip())
        client.delete_volume(str(cls.volume_to_detach['id']).strip())
        resp, cls.sg = \
        cls.security_groups_client.delete_security_group(cls.sg_id)

    def tearDown(self):
        super(ServerRescueTestJSON, self).tearDown()

    def _detach(self, server_id, volume_id):
        self.servers_client.detach_volume(server_id, volume_id)
        self.volumes_extensions_client.wait_for_volume_status(volume_id,
                                                              'available')

    def _delete(self, volume_id):
        self.volumes_extensions_client.delete_volume(volume_id)

    def _unrescue(self, server_id):
        resp, body = self.servers_client.unrescue_server(server_id)
        self.assertEqual(202, resp.status)
        self.servers_client.wait_for_server_status(server_id, 'ACTIVE')

    @attr(type='smoke')
    def test_rescue_unrescue_instance(self):
        resp, body = self.servers_client.rescue_server(
            self.server_id, self.password)
        self.assertEqual(200, resp.status)
        self.servers_client.wait_for_server_status(self.server_id, 'RESCUE')
        resp, body = self.servers_client.unrescue_server(self.server_id)
        self.assertEqual(202, resp.status)
        self.servers_client.wait_for_server_status(self.server_id, 'ACTIVE')

    @attr(type='negative')
    def test_rescued_vm_reboot(self):
        self.assertRaises(exceptions.Duplicate, self.servers_client.reboot,
                          self.rescue_id, 'HARD')

    @attr(type='negative')
    def test_rescued_vm_rebuild(self):
        self.assertRaises(exceptions.Duplicate,
                          self.servers_client.rebuild,
                          self.rescue_id,
                          self.image_ref_alt)

    @attr(type='negative')
    def test_rescued_vm_attach_volume(self):
        # Rescue the server
        self.servers_client.rescue_server(self.server_id, self.password)
        self.servers_client.wait_for_server_status(self.server_id, 'RESCUE')
        self.addCleanup(self._unrescue, self.server_id)

        # Attach the volume to the server
        self.assertRaises(exceptions.Duplicate,
                          self.servers_client.attach_volume,
                          self.server_id,
                          self.volume_to_attach['id'],
                          device='/dev/%s' % self.device)

    @attr(type='negative')
    def test_rescued_vm_detach_volume(self):
        # Attach the volume to the server
        self.servers_client.attach_volume(self.server_id,
                                          self.volume_to_detach['id'],
                                          device='/dev/%s' % self.device)
        self.volumes_extensions_client.wait_for_volume_status(
                self.volume_to_detach['id'], 'in-use')

        # Rescue the server
        self.servers_client.rescue_server(self.server_id, self.password)
        self.servers_client.wait_for_server_status(self.server_id, 'RESCUE')
        #addCleanup is a LIFO queue
        self.addCleanup(self._detach, self.server_id,
                        self.volume_to_detach['id'])
        self.addCleanup(self._unrescue, self.server_id)

        # Detach the volume from the server expecting failure
        self.assertRaises(exceptions.Duplicate,
                          self.servers_client.detach_volume,
                          self.server_id,
                          self.volume_to_detach['id'])

    @attr(type='positive')
    def test_rescued_vm_associate_dissociate_floating_ip(self):
        # Rescue the server
        self.servers_client.rescue_server(
            self.server_id, self.password)
        self.servers_client.wait_for_server_status(self.server_id, 'RESCUE')
        self.addCleanup(self._unrescue, self.server_id)

        #Association of floating IP to a rescued vm
        client = self.floating_ips_client
        resp, body =\
        client.associate_floating_ip_to_server(self.floating_ip,
                                               self.server_id)
        self.assertEqual(202, resp.status)

        #Disassociation of floating IP that was associated in this method
        resp, body = \
            client.disassociate_floating_ip_from_server(self.floating_ip,
                                                        self.server_id)
        self.assertEqual(202, resp.status)

    @attr(type='positive')
    @testtools.skip("Skipped until Bug #1126257 is resolved")
    def test_rescued_vm_add_remove_security_group(self):
        #Add Security group
        resp, body = self.servers_client.add_security_group(self.server_id,
                                                            self.sg_name)
        self.assertEqual(202, resp.status)

        #Delete Security group
        resp, body = self.servers_client.remove_security_group(self.server_id,
                                                               self.sg_id)
        self.assertEqual(202, resp.status)

        # Unrescue the server
        resp, body = self.servers_client.unrescue_server(self.server_id)
        self.assertEqual(202, resp.status)
        self.servers_client.wait_for_server_status(self.server_id, 'ACTIVE')


class ServerRescueTestXML(ServerRescueTestJSON):
    _interface = 'xml'

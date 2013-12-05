# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2012 OpenStack Foundation
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

from tempest.api import compute
from tempest.api.compute import base
from tempest.test import attr


class ServerDiskConfigTestJSON(base.BaseV2ComputeTest):
    _interface = 'json'

    @classmethod
    def setUpClass(cls):
        if not compute.DISK_CONFIG_ENABLED:
            msg = "DiskConfig extension not enabled."
            raise cls.skipException(msg)
        super(ServerDiskConfigTestJSON, cls).setUpClass()
        cls.client = cls.os.servers_client
        resp, server = cls.create_test_server(wait_until='ACTIVE')
        cls.server_id = server['id']

    def _update_server_with_disk_config(self, disk_config):
        resp, server = self.client.get_server(self.server_id)
        if disk_config != server['OS-DCF:diskConfig']:
            resp, server = self.client.update_server(self.server_id,
                                                     disk_config=disk_config)
            self.assertEqual(200, resp.status)
            self.client.wait_for_server_status(server['id'], 'ACTIVE')
            resp, server = self.client.get_server(server['id'])
            self.assertEqual(disk_config, server['OS-DCF:diskConfig'])

    @attr(type='gate')
    def test_rebuild_server_with_manual_disk_config(self):
        # A server should be rebuilt using the manual disk config option
        self._update_server_with_disk_config(disk_config='AUTO')

        resp, server = self.client.rebuild(self.server_id,
                                           self.image_ref_alt,
                                           disk_config='MANUAL')

        # Wait for the server to become active
        self.client.wait_for_server_status(server['id'], 'ACTIVE')

        # Verify the specified attributes are set correctly
        resp, server = self.client.get_server(server['id'])
        self.assertEqual('MANUAL', server['OS-DCF:diskConfig'])

    @attr(type='gate')
    def test_rebuild_server_with_auto_disk_config(self):
        # A server should be rebuilt using the auto disk config option
        self._update_server_with_disk_config(disk_config='MANUAL')

        resp, server = self.client.rebuild(self.server_id,
                                           self.image_ref_alt,
                                           disk_config='AUTO')

        # Wait for the server to become active
        self.client.wait_for_server_status(server['id'], 'ACTIVE')

        # Verify the specified attributes are set correctly
        resp, server = self.client.get_server(server['id'])
        self.assertEqual('AUTO', server['OS-DCF:diskConfig'])

    def _get_alternative_flavor(self):
        resp, server = self.client.get_server(self.server_id)

        if server['flavor']['id'] == self.flavor_ref:
            return self.flavor_ref_alt
        else:
            return self.flavor_ref

    @testtools.skipUnless(compute.RESIZE_AVAILABLE, 'Resize not available.')
    @attr(type='gate')
    def test_resize_server_from_manual_to_auto(self):
        # A server should be resized from manual to auto disk config
        self._update_server_with_disk_config(disk_config='MANUAL')

        # Resize with auto option
        flavor_id = self._get_alternative_flavor()
        self.client.resize(self.server_id, flavor_id, disk_config='AUTO')
        self.client.wait_for_server_status(self.server_id, 'VERIFY_RESIZE')
        self.client.confirm_resize(self.server_id)
        self.client.wait_for_server_status(self.server_id, 'ACTIVE')

        resp, server = self.client.get_server(self.server_id)
        self.assertEqual('AUTO', server['OS-DCF:diskConfig'])

    @testtools.skipUnless(compute.RESIZE_AVAILABLE, 'Resize not available.')
    @attr(type='gate')
    def test_resize_server_from_auto_to_manual(self):
        # A server should be resized from auto to manual disk config
        self._update_server_with_disk_config(disk_config='AUTO')

        # Resize with manual option
        flavor_id = self._get_alternative_flavor()
        self.client.resize(self.server_id, flavor_id, disk_config='MANUAL')
        self.client.wait_for_server_status(self.server_id, 'VERIFY_RESIZE')
        self.client.confirm_resize(self.server_id)
        self.client.wait_for_server_status(self.server_id, 'ACTIVE')

        resp, server = self.client.get_server(self.server_id)
        self.assertEqual('MANUAL', server['OS-DCF:diskConfig'])

    @attr(type='gate')
    def test_update_server_from_auto_to_manual(self):
        # A server should be updated from auto to manual disk config
        self._update_server_with_disk_config(disk_config='AUTO')

        # Update the disk_config attribute to manual
        resp, server = self.client.update_server(self.server_id,
                                                 disk_config='MANUAL')
        self.assertEqual(200, resp.status)
        self.client.wait_for_server_status(server['id'], 'ACTIVE')

        # Verify the disk_config attribute is set correctly
        resp, server = self.client.get_server(server['id'])
        self.assertEqual('MANUAL', server['OS-DCF:diskConfig'])


class ServerDiskConfigTestXML(ServerDiskConfigTestJSON):
    _interface = 'xml'

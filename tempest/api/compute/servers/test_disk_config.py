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

from tempest.api.compute import base
from tempest.common import waiters
from tempest import config
from tempest import test

CONF = config.CONF


class ServerDiskConfigTestJSON(base.BaseV2ComputeTest):

    @classmethod
    def skip_checks(cls):
        super(ServerDiskConfigTestJSON, cls).skip_checks()
        if not CONF.compute_feature_enabled.disk_config:
            msg = "DiskConfig extension not enabled."
            raise cls.skipException(msg)

    @classmethod
    def setup_clients(cls):
        super(ServerDiskConfigTestJSON, cls).setup_clients()
        cls.client = cls.os.servers_client

    @classmethod
    def resource_setup(cls):
        super(ServerDiskConfigTestJSON, cls).resource_setup()
        server = cls.create_test_server(wait_until='ACTIVE')
        cls.server_id = server['id']

    def _update_server_with_disk_config(self, disk_config):
        server = self.client.show_server(self.server_id)['server']
        if disk_config != server['OS-DCF:diskConfig']:
            server = self.client.update_server(
                self.server_id, disk_config=disk_config)['server']
            waiters.wait_for_server_status(self.client, server['id'], 'ACTIVE')
            server = self.client.show_server(server['id'])['server']
            self.assertEqual(disk_config, server['OS-DCF:diskConfig'])

    @test.idempotent_id('bef56b09-2e8c-4883-a370-4950812f430e')
    def test_rebuild_server_with_manual_disk_config(self):
        # A server should be rebuilt using the manual disk config option
        self._update_server_with_disk_config(disk_config='AUTO')

        server = self.client.rebuild_server(self.server_id,
                                            self.image_ref_alt,
                                            disk_config='MANUAL')['server']

        # Wait for the server to become active
        waiters.wait_for_server_status(self.client, server['id'], 'ACTIVE')

        # Verify the specified attributes are set correctly
        server = self.client.show_server(server['id'])['server']
        self.assertEqual('MANUAL', server['OS-DCF:diskConfig'])

    @test.idempotent_id('9c9fae77-4feb-402f-8450-bf1c8b609713')
    def test_rebuild_server_with_auto_disk_config(self):
        # A server should be rebuilt using the auto disk config option
        self._update_server_with_disk_config(disk_config='MANUAL')

        server = self.client.rebuild_server(self.server_id,
                                            self.image_ref_alt,
                                            disk_config='AUTO')['server']

        # Wait for the server to become active
        waiters.wait_for_server_status(self.client, server['id'], 'ACTIVE')

        # Verify the specified attributes are set correctly
        server = self.client.show_server(server['id'])['server']
        self.assertEqual('AUTO', server['OS-DCF:diskConfig'])

    def _get_alternative_flavor(self):
        server = self.client.show_server(self.server_id)['server']

        if server['flavor']['id'] == self.flavor_ref:
            return self.flavor_ref_alt
        else:
            return self.flavor_ref

    @test.idempotent_id('414e7e93-45b5-44bc-8e03-55159c6bfc97')
    @testtools.skipUnless(CONF.compute_feature_enabled.resize,
                          'Resize not available.')
    def test_resize_server_from_manual_to_auto(self):
        # A server should be resized from manual to auto disk config
        self._update_server_with_disk_config(disk_config='MANUAL')

        # Resize with auto option
        flavor_id = self._get_alternative_flavor()
        self.client.resize_server(self.server_id, flavor_id,
                                  disk_config='AUTO')
        waiters.wait_for_server_status(self.client, self.server_id,
                                       'VERIFY_RESIZE')
        self.client.confirm_resize_server(self.server_id)
        waiters.wait_for_server_status(self.client, self.server_id, 'ACTIVE')

        server = self.client.show_server(self.server_id)['server']
        self.assertEqual('AUTO', server['OS-DCF:diskConfig'])

    @test.idempotent_id('693d16f3-556c-489a-8bac-3d0ca2490bad')
    @testtools.skipUnless(CONF.compute_feature_enabled.resize,
                          'Resize not available.')
    def test_resize_server_from_auto_to_manual(self):
        # A server should be resized from auto to manual disk config
        self._update_server_with_disk_config(disk_config='AUTO')

        # Resize with manual option
        flavor_id = self._get_alternative_flavor()
        self.client.resize_server(self.server_id, flavor_id,
                                  disk_config='MANUAL')
        waiters.wait_for_server_status(self.client, self.server_id,
                                       'VERIFY_RESIZE')
        self.client.confirm_resize_server(self.server_id)
        waiters.wait_for_server_status(self.client, self.server_id, 'ACTIVE')

        server = self.client.show_server(self.server_id)['server']
        self.assertEqual('MANUAL', server['OS-DCF:diskConfig'])

    @test.idempotent_id('5ef18867-358d-4de9-b3c9-94d4ba35742f')
    def test_update_server_from_auto_to_manual(self):
        # A server should be updated from auto to manual disk config
        self._update_server_with_disk_config(disk_config='AUTO')

        # Update the disk_config attribute to manual
        server = self.client.update_server(self.server_id,
                                           disk_config='MANUAL')['server']
        waiters.wait_for_server_status(self.client, server['id'], 'ACTIVE')

        # Verify the disk_config attribute is set correctly
        server = self.client.show_server(server['id'])['server']
        self.assertEqual('MANUAL', server['OS-DCF:diskConfig'])

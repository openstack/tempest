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
from tempest.common import compute
from tempest.common import utils
from tempest.common import waiters
from tempest import config
from tempest.lib import decorators

CONF = config.CONF


class DeleteServersTestJSON(base.BaseV2ComputeTest):
    """Test deleting servers in various states"""
    create_default_network = True

    # NOTE: Server creations of each test class should be under 10
    # for preventing "Quota exceeded for instances"

    @classmethod
    def setup_clients(cls):
        super(DeleteServersTestJSON, cls).setup_clients()
        cls.client = cls.servers_client

    @decorators.idempotent_id('9e6e0c87-3352-42f7-9faf-5d6210dbd159')
    def test_delete_server_while_in_building_state(self):
        """Test deleting a server while it's VM state is Building"""
        server = self.create_test_server(wait_until='BUILD')
        self.client.delete_server(server['id'])
        waiters.wait_for_server_termination(self.client, server['id'])

    @decorators.idempotent_id('925fdfb4-5b13-47ea-ac8a-c36ae6fddb05')
    def test_delete_active_server(self):
        """Test deleting a server while it's VM state is Active"""
        server = self.create_test_server(wait_until='ACTIVE')
        self.client.delete_server(server['id'])
        waiters.wait_for_server_termination(self.client, server['id'])

    @decorators.idempotent_id('546d368c-bb6c-4645-979a-83ed16f3a6be')
    def test_delete_server_while_in_shutoff_state(self):
        """Test deleting a server while it's VM state is Shutoff"""
        server = self.create_test_server(wait_until='ACTIVE')
        self.client.stop_server(server['id'])
        waiters.wait_for_server_status(self.client, server['id'], 'SHUTOFF')
        self.client.delete_server(server['id'])
        waiters.wait_for_server_termination(self.client, server['id'])

    @decorators.idempotent_id('943bd6e8-4d7a-4904-be83-7a6cc2d4213b')
    @testtools.skipUnless(CONF.compute_feature_enabled.pause,
                          'Pause is not available.')
    def test_delete_server_while_in_pause_state(self):
        """Test deleting a server while it's VM state is Pause"""
        server = self.create_test_server(wait_until='ACTIVE')
        self.client.pause_server(server['id'])
        waiters.wait_for_server_status(self.client, server['id'], 'PAUSED')
        self.client.delete_server(server['id'])
        waiters.wait_for_server_termination(self.client, server['id'])

    @decorators.idempotent_id('1f82ebd3-8253-4f4e-b93f-de9b7df56d8b')
    @testtools.skipUnless(CONF.compute_feature_enabled.suspend,
                          'Suspend is not available.')
    def test_delete_server_while_in_suspended_state(self):
        """Test deleting a server while it's VM state is Suspended"""
        server = self.create_test_server(wait_until='ACTIVE')
        self.client.suspend_server(server['id'])
        waiters.wait_for_server_status(self.client, server['id'], 'SUSPENDED')
        self.client.delete_server(server['id'])
        waiters.wait_for_server_termination(self.client, server['id'])

    @decorators.idempotent_id('bb0cb402-09dd-4947-b6e5-5e7e1cfa61ad')
    @testtools.skipUnless(CONF.compute_feature_enabled.shelve,
                          'Shelve is not available.')
    def test_delete_server_while_in_shelved_state(self):
        """Test deleting a server while it's VM state is Shelved"""
        server = self.create_test_server(wait_until='ACTIVE')
        compute.shelve_server(self.client, server['id'])

        self.client.delete_server(server['id'])
        waiters.wait_for_server_termination(self.client, server['id'])

    @decorators.idempotent_id('ab0c38b4-cdd8-49d3-9b92-0cb898723c01')
    @testtools.skipIf(not CONF.compute_feature_enabled.resize,
                      'Resize not available.')
    def test_delete_server_while_in_verify_resize_state(self):
        """Test deleting a server while it's VM state is VERIFY_RESIZE"""
        server = self.create_test_server(wait_until='ACTIVE')
        body = self.client.resize_server(server['id'], self.flavor_ref_alt)
        request_id = body.response['x-openstack-request-id']
        waiters.wait_for_server_status(
            self.client, server['id'], 'VERIFY_RESIZE', request_id=request_id)
        body = self.client.delete_server(server['id'])
        request_id = body.response['x-openstack-request-id']
        waiters.wait_for_server_termination(
            self.client, server['id'], request_id=request_id)

    @decorators.idempotent_id('d0f3f0d6-d9b6-4a32-8da4-23015dcab23c')
    @utils.services('volume')
    def test_delete_server_while_in_attached_volume(self):
        """Test deleting a server while a volume is attached to it"""
        server = self.create_test_server(wait_until='ACTIVE')

        volume = self.create_volume()
        self.attach_volume(server, volume)

        self.client.delete_server(server['id'])
        waiters.wait_for_server_termination(self.client, server['id'])
        waiters.wait_for_volume_resource_status(self.volumes_client,
                                                volume['id'], 'available')

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
from tempest import config
from tempest import test

CONF = config.CONF


class DeleteServersTestJSON(base.BaseV2ComputeTest):

    # NOTE: Server creations of each test class should be under 10
    # for preventing "Quota exceeded for instances"

    @classmethod
    def setup_clients(cls):
        super(DeleteServersTestJSON, cls).setup_clients()
        cls.client = cls.servers_client

    @test.attr(type='gate')
    @test.idempotent_id('9e6e0c87-3352-42f7-9faf-5d6210dbd159')
    def test_delete_server_while_in_building_state(self):
        # Delete a server while it's VM state is Building
        server = self.create_test_server(wait_until='BUILD')
        self.client.delete_server(server['id'])
        self.client.wait_for_server_termination(server['id'])

    @test.attr(type='gate')
    @test.idempotent_id('925fdfb4-5b13-47ea-ac8a-c36ae6fddb05')
    def test_delete_active_server(self):
        # Delete a server while it's VM state is Active
        server = self.create_test_server(wait_until='ACTIVE')
        self.client.delete_server(server['id'])
        self.client.wait_for_server_termination(server['id'])

    @test.attr(type='gate')
    @test.idempotent_id('546d368c-bb6c-4645-979a-83ed16f3a6be')
    def test_delete_server_while_in_shutoff_state(self):
        # Delete a server while it's VM state is Shutoff
        server = self.create_test_server(wait_until='ACTIVE')
        self.client.stop(server['id'])
        self.client.wait_for_server_status(server['id'], 'SHUTOFF')
        self.client.delete_server(server['id'])
        self.client.wait_for_server_termination(server['id'])

    @test.idempotent_id('943bd6e8-4d7a-4904-be83-7a6cc2d4213b')
    @testtools.skipUnless(CONF.compute_feature_enabled.pause,
                          'Pause is not available.')
    @test.attr(type='gate')
    def test_delete_server_while_in_pause_state(self):
        # Delete a server while it's VM state is Pause
        server = self.create_test_server(wait_until='ACTIVE')
        self.client.pause_server(server['id'])
        self.client.wait_for_server_status(server['id'], 'PAUSED')
        self.client.delete_server(server['id'])
        self.client.wait_for_server_termination(server['id'])

    @test.idempotent_id('1f82ebd3-8253-4f4e-b93f-de9b7df56d8b')
    @testtools.skipUnless(CONF.compute_feature_enabled.suspend,
                          'Suspend is not available.')
    @test.attr(type='gate')
    def test_delete_server_while_in_suspended_state(self):
        # Delete a server while it's VM state is Suspended
        server = self.create_test_server(wait_until='ACTIVE')
        self.client.suspend_server(server['id'])
        self.client.wait_for_server_status(server['id'], 'SUSPENDED')
        self.client.delete_server(server['id'])
        self.client.wait_for_server_termination(server['id'])

    @test.idempotent_id('bb0cb402-09dd-4947-b6e5-5e7e1cfa61ad')
    @testtools.skipUnless(CONF.compute_feature_enabled.shelve,
                          'Shelve is not available.')
    @test.attr(type='gate')
    def test_delete_server_while_in_shelved_state(self):
        # Delete a server while it's VM state is Shelved
        server = self.create_test_server(wait_until='ACTIVE')
        self.client.shelve_server(server['id'])

        offload_time = CONF.compute.shelved_offload_time
        if offload_time >= 0:
            self.client.wait_for_server_status(server['id'],
                                               'SHELVED_OFFLOADED',
                                               extra_timeout=offload_time)
        else:
            self.client.wait_for_server_status(server['id'],
                                               'SHELVED')
        self.client.delete_server(server['id'])
        self.client.wait_for_server_termination(server['id'])

    @test.idempotent_id('ab0c38b4-cdd8-49d3-9b92-0cb898723c01')
    @testtools.skipIf(not CONF.compute_feature_enabled.resize,
                      'Resize not available.')
    @test.attr(type='gate')
    def test_delete_server_while_in_verify_resize_state(self):
        # Delete a server while it's VM state is VERIFY_RESIZE
        server = self.create_test_server(wait_until='ACTIVE')
        self.client.resize(server['id'], self.flavor_ref_alt)
        self.client.wait_for_server_status(server['id'], 'VERIFY_RESIZE')
        self.client.delete_server(server['id'])
        self.client.wait_for_server_termination(server['id'])

    @test.idempotent_id('d0f3f0d6-d9b6-4a32-8da4-23015dcab23c')
    @test.services('volume')
    @test.attr(type='gate')
    def test_delete_server_while_in_attached_volume(self):
        # Delete a server while a volume is attached to it
        volumes_client = self.volumes_extensions_client
        device = '/dev/%s' % CONF.compute.volume_device_name
        server = self.create_test_server(wait_until='ACTIVE')

        volume = volumes_client.create_volume()
        self.addCleanup(volumes_client.delete_volume, volume['id'])
        volumes_client.wait_for_volume_status(volume['id'], 'available')
        self.client.attach_volume(server['id'],
                                  volume['id'],
                                  device=device)
        volumes_client.wait_for_volume_status(volume['id'], 'in-use')

        self.client.delete_server(server['id'])
        self.client.wait_for_server_termination(server['id'])
        volumes_client.wait_for_volume_status(volume['id'], 'available')


class DeleteServersAdminTestJSON(base.BaseV2ComputeAdminTest):
    # NOTE: Server creations of each test class should be under 10
    # for preventing "Quota exceeded for instances".

    @classmethod
    def setup_clients(cls):
        super(DeleteServersAdminTestJSON, cls).setup_clients()
        cls.non_admin_client = cls.servers_client
        cls.admin_client = cls.os_adm.servers_client

    @test.attr(type='gate')
    @test.idempotent_id('99774678-e072-49d1-9d2a-49a59bc56063')
    def test_delete_server_while_in_error_state(self):
        # Delete a server while it's VM state is error
        server = self.create_test_server(wait_until='ACTIVE')
        self.admin_client.reset_state(server['id'], state='error')
        # Verify server's state
        server = self.non_admin_client.get_server(server['id'])
        self.assertEqual(server['status'], 'ERROR')
        self.non_admin_client.delete_server(server['id'])
        self.servers_client.wait_for_server_termination(server['id'],
                                                        ignore_error=True)

    @test.attr(type='gate')
    @test.idempotent_id('73177903-6737-4f27-a60c-379e8ae8cf48')
    def test_admin_delete_servers_of_others(self):
        # Administrator can delete servers of others
        server = self.create_test_server(wait_until='ACTIVE')
        self.admin_client.delete_server(server['id'])
        self.servers_client.wait_for_server_termination(server['id'])

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
from tempest.common import waiters
from tempest import config
from tempest.lib import exceptions
from tempest import test

CONF = config.CONF


class MigrationsAdminTest(base.BaseV2ComputeAdminTest):

    @classmethod
    def setup_clients(cls):
        super(MigrationsAdminTest, cls).setup_clients()
        cls.client = cls.os_adm.migrations_client
        cls.flavors_admin_client = cls.os_adm.flavors_client

    @test.idempotent_id('75c0b83d-72a0-4cf8-a153-631e83e7d53f')
    def test_list_migrations(self):
        # Admin can get the migrations list
        self.client.list_migrations()

    @test.idempotent_id('1b512062-8093-438e-b47a-37d2f597cd64')
    @testtools.skipUnless(CONF.compute_feature_enabled.resize,
                          'Resize not available.')
    def test_list_migrations_in_flavor_resize_situation(self):
        # Admin can get the migrations list which contains the resized server
        server = self.create_test_server(wait_until="ACTIVE")
        server_id = server['id']

        self.servers_client.resize_server(server_id, self.flavor_ref_alt)
        waiters.wait_for_server_status(self.servers_client,
                                       server_id, 'VERIFY_RESIZE')
        self.servers_client.confirm_resize_server(server_id)
        waiters.wait_for_server_status(self.servers_client,
                                       server_id, 'ACTIVE')

        body = self.client.list_migrations()['migrations']

        instance_uuids = [x['instance_uuid'] for x in body]
        self.assertIn(server_id, instance_uuids)

    def _flavor_clean_up(self, flavor_id):
        try:
            self.flavors_admin_client.delete_flavor(flavor_id)
            self.flavors_admin_client.wait_for_resource_deletion(flavor_id)
        except exceptions.NotFound:
            pass

    @test.idempotent_id('33f1fec3-ba18-4470-8e4e-1d888e7c3593')
    @testtools.skipUnless(CONF.compute_feature_enabled.resize,
                          'Resize not available.')
    def test_resize_server_revert_deleted_flavor(self):
        # Tests that we can revert the resize on an instance whose original
        # flavor has been deleted.

        # First we have to create a flavor that we can delete so make a copy
        # of the normal flavor from which we'd create a server.
        flavor = self.flavors_admin_client.show_flavor(
            self.flavor_ref)['flavor']
        flavor = self.flavors_admin_client.create_flavor(
            name=data_utils.rand_name('test_resize_flavor_'),
            ram=flavor['ram'],
            disk=flavor['disk'],
            vcpus=flavor['vcpus']
        )['flavor']
        self.addCleanup(self._flavor_clean_up, flavor['id'])

        # Now boot a server with the copied flavor.
        server = self.create_test_server(
            wait_until='ACTIVE', flavor=flavor['id'])

        # Delete the flavor we used to boot the instance.
        self._flavor_clean_up(flavor['id'])

        # Now resize the server and wait for it to go into verify state.
        self.servers_client.resize_server(server['id'], self.flavor_ref_alt)
        waiters.wait_for_server_status(self.servers_client, server['id'],
                                       'VERIFY_RESIZE')

        # Now revert the resize, it should be OK even though the original
        # flavor used to boot the server was deleted.
        self.servers_client.revert_resize_server(server['id'])
        waiters.wait_for_server_status(self.servers_client, server['id'],
                                       'ACTIVE')

        server = self.servers_client.show_server(server['id'])['server']
        self.assertEqual(flavor['id'], server['flavor']['id'])

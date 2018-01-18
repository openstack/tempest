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
from tempest.common import waiters
from tempest import config
from tempest.lib.common.utils import data_utils
from tempest.lib import decorators
from tempest.lib import exceptions

CONF = config.CONF


class MigrationsAdminTest(base.BaseV2ComputeAdminTest):

    @classmethod
    def setup_clients(cls):
        super(MigrationsAdminTest, cls).setup_clients()
        cls.client = cls.os_admin.migrations_client

    @decorators.idempotent_id('75c0b83d-72a0-4cf8-a153-631e83e7d53f')
    def test_list_migrations(self):
        # Admin can get the migrations list
        self.client.list_migrations()

    @decorators.idempotent_id('1b512062-8093-438e-b47a-37d2f597cd64')
    @testtools.skipUnless(CONF.compute_feature_enabled.resize,
                          'Resize not available.')
    def test_list_migrations_in_flavor_resize_situation(self):
        # Admin can get the migrations list which contains the resized server
        server = self.create_test_server(wait_until="ACTIVE")
        server_id = server['id']

        self.resize_server(server_id, self.flavor_ref_alt)

        body = self.client.list_migrations()['migrations']

        instance_uuids = [x['instance_uuid'] for x in body]
        self.assertIn(server_id, instance_uuids)

    def _flavor_clean_up(self, flavor_id):
        try:
            self.admin_flavors_client.delete_flavor(flavor_id)
            self.admin_flavors_client.wait_for_resource_deletion(flavor_id)
        except exceptions.NotFound:
            pass

    @decorators.idempotent_id('33f1fec3-ba18-4470-8e4e-1d888e7c3593')
    @testtools.skipUnless(CONF.compute_feature_enabled.resize,
                          'Resize not available.')
    def test_resize_server_revert_deleted_flavor(self):
        # Tests that we can revert the resize on an instance whose original
        # flavor has been deleted.

        # First we have to create a flavor that we can delete so make a copy
        # of the normal flavor from which we'd create a server.
        flavor = self.admin_flavors_client.show_flavor(
            self.flavor_ref)['flavor']
        flavor = self.admin_flavors_client.create_flavor(
            name=data_utils.rand_name('test_resize_flavor_'),
            ram=flavor['ram'],
            disk=flavor['disk'],
            vcpus=flavor['vcpus']
        )['flavor']
        self.addCleanup(self._flavor_clean_up, flavor['id'])

        # Set extra specs same as self.flavor_ref for the created flavor,
        # because the environment may need some special extra specs to
        # create server which should have been contained in
        # self.flavor_ref.
        extra_spec_keys = self.admin_flavors_client.list_flavor_extra_specs(
            self.flavor_ref)['extra_specs']
        if extra_spec_keys:
            self.admin_flavors_client.set_flavor_extra_spec(
                flavor['id'], **extra_spec_keys)

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

    def _test_cold_migrate_server(self, revert=False):
        if CONF.compute.min_compute_nodes < 2:
            msg = "Less than 2 compute nodes, skipping multinode tests."
            raise self.skipException(msg)

        server = self.create_test_server(wait_until="ACTIVE")
        src_host = self.admin_servers_client.show_server(
            server['id'])['server']['OS-EXT-SRV-ATTR:host']

        self.admin_servers_client.migrate_server(server['id'])

        waiters.wait_for_server_status(self.servers_client,
                                       server['id'], 'VERIFY_RESIZE')

        if revert:
            self.servers_client.revert_resize_server(server['id'])
            assert_func = self.assertEqual
        else:
            self.servers_client.confirm_resize_server(server['id'])
            assert_func = self.assertNotEqual

        waiters.wait_for_server_status(self.servers_client,
                                       server['id'], 'ACTIVE')
        dst_host = self.admin_servers_client.show_server(
            server['id'])['server']['OS-EXT-SRV-ATTR:host']
        assert_func(src_host, dst_host)

    @decorators.idempotent_id('4bf0be52-3b6f-4746-9a27-3143636fe30d')
    @testtools.skipUnless(CONF.compute_feature_enabled.cold_migration,
                          'Cold migration not available.')
    def test_cold_migration(self):
        self._test_cold_migrate_server(revert=False)

    @decorators.idempotent_id('caa1aa8b-f4ef-4374-be0d-95f001c2ac2d')
    @testtools.skipUnless(CONF.compute_feature_enabled.cold_migration,
                          'Cold migration not available.')
    def test_revert_cold_migration(self):
        self._test_cold_migrate_server(revert=True)

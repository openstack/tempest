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
from tempest import config
from tempest import test

CONF = config.CONF


class MigrationsAdminTest(base.BaseV2ComputeAdminTest):

    @classmethod
    def setup_clients(cls):
        super(MigrationsAdminTest, cls).setup_clients()
        cls.client = cls.os_adm.migrations_client

    @test.attr(type='gate')
    @test.idempotent_id('75c0b83d-72a0-4cf8-a153-631e83e7d53f')
    def test_list_migrations(self):
        # Admin can get the migrations list
        self.client.list_migrations()

    @test.idempotent_id('1b512062-8093-438e-b47a-37d2f597cd64')
    @testtools.skipUnless(CONF.compute_feature_enabled.resize,
                          'Resize not available.')
    @test.attr(type='gate')
    def test_list_migrations_in_flavor_resize_situation(self):
        # Admin can get the migrations list which contains the resized server
        server = self.create_test_server(wait_until="ACTIVE")
        server_id = server['id']

        self.servers_client.resize(server_id, self.flavor_ref_alt)
        self.servers_client.wait_for_server_status(server_id, 'VERIFY_RESIZE')
        self.servers_client.confirm_resize(server_id)
        self.servers_client.wait_for_server_status(server_id, 'ACTIVE')

        body = self.client.list_migrations()

        instance_uuids = [x['instance_uuid'] for x in body]
        self.assertIn(server_id, instance_uuids)

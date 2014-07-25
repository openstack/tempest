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


class MigrationsAdminV3Test(base.BaseV3ComputeAdminTest):

    @test.attr(type='gate')
    def test_list_migrations(self):
        # Admin can get the migrations list
        resp, _ = self.migrations_admin_client.list_migrations()
        self.assertEqual(200, resp.status)

    @testtools.skipUnless(CONF.compute_feature_enabled.resize,
                          'Resize not available.')
    @test.attr(type='gate')
    def test_list_migrations_in_flavor_resize_situation(self):
        # Admin can get the migrations list which contains the resized server
        resp, server = self.create_test_server(wait_until="ACTIVE")
        server_id = server['id']

        resp, _ = self.servers_client.resize(server_id, self.flavor_ref_alt)
        self.assertEqual(202, resp.status)
        self.servers_client.wait_for_server_status(server_id, 'VERIFY_RESIZE')
        self.servers_client.confirm_resize(server_id)
        self.servers_client.wait_for_server_status(server_id, 'ACTIVE')

        resp, body = self.migrations_admin_client.list_migrations()
        self.assertEqual(200, resp.status)

        instance_uuids = [x['instance_uuid'] for x in body]
        self.assertIn(server_id, instance_uuids)

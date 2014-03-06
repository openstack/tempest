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

from tempest.api.compute import base
from tempest import test


class ServerRescueV3Test(base.BaseV3ComputeTest):

    @classmethod
    def setUpClass(cls):
        super(ServerRescueV3Test, cls).setUpClass()

        # Server for positive tests
        resp, server = cls.create_test_server(wait_until='BUILD')
        cls.server_id = server['id']
        cls.password = server['admin_password']
        cls.servers_client.wait_for_server_status(cls.server_id, 'ACTIVE')

    @test.attr(type='smoke')
    def test_rescue_unrescue_instance(self):
        resp, body = self.servers_client.rescue_server(
            self.server_id, admin_password=self.password)
        self.assertEqual(202, resp.status)
        self.servers_client.wait_for_server_status(self.server_id, 'RESCUE')
        resp, body = self.servers_client.unrescue_server(self.server_id)
        self.assertEqual(202, resp.status)
        self.servers_client.wait_for_server_status(self.server_id, 'ACTIVE')

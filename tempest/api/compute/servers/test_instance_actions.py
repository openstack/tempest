# Copyright 2013 NEC Corporation
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


class InstanceActionsTestJSON(base.BaseV2ComputeTest):

    @classmethod
    def setup_clients(cls):
        super(InstanceActionsTestJSON, cls).setup_clients()
        cls.client = cls.servers_client

    @classmethod
    def resource_setup(cls):
        super(InstanceActionsTestJSON, cls).resource_setup()
        server = cls.create_test_server(wait_until='ACTIVE')
        cls.request_id = server.response['x-compute-request-id']
        cls.server_id = server['id']

    @test.attr(type='gate')
    @test.idempotent_id('77ca5cc5-9990-45e0-ab98-1de8fead201a')
    def test_list_instance_actions(self):
        # List actions of the provided server
        self.client.reboot(self.server_id, 'HARD')
        self.client.wait_for_server_status(self.server_id, 'ACTIVE')

        body = self.client.list_instance_actions(self.server_id)
        self.assertTrue(len(body) == 2, str(body))
        self.assertTrue(any([i for i in body if i['action'] == 'create']))
        self.assertTrue(any([i for i in body if i['action'] == 'reboot']))

    @test.attr(type='gate')
    @test.idempotent_id('aacc71ca-1d70-4aa5-bbf6-0ff71470e43c')
    def test_get_instance_action(self):
        # Get the action details of the provided server
        body = self.client.get_instance_action(self.server_id,
                                               self.request_id)
        self.assertEqual(self.server_id, body['instance_uuid'])
        self.assertEqual('create', body['action'])

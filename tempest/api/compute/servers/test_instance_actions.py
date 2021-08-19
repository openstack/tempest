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
from tempest.common import waiters
from tempest.lib import decorators


class InstanceActionsTestJSON(base.BaseV2ComputeTest):
    """Test instance actions API"""

    create_default_network = True

    @classmethod
    def setup_clients(cls):
        super(InstanceActionsTestJSON, cls).setup_clients()
        cls.client = cls.servers_client

    @classmethod
    def resource_setup(cls):
        super(InstanceActionsTestJSON, cls).resource_setup()
        cls.server = cls.create_test_server(wait_until='ACTIVE')
        cls.request_id = cls.server.response['x-compute-request-id']

    @decorators.idempotent_id('77ca5cc5-9990-45e0-ab98-1de8fead201a')
    def test_list_instance_actions(self):
        """Test listing actions of the provided server"""
        self.reboot_server(self.server['id'], type='HARD')

        body = (self.client.list_instance_actions(self.server['id'])
                ['instanceActions'])
        self.assertEqual(len(body), 2, str(body))
        self.assertEqual(sorted([i['action'] for i in body]),
                         ['create', 'reboot'])

    @decorators.idempotent_id('aacc71ca-1d70-4aa5-bbf6-0ff71470e43c')
    def test_get_instance_action(self):
        """Test getting the action details of the provided server"""
        body = self.client.show_instance_action(
            self.server['id'], self.request_id)['instanceAction']
        self.assertEqual(self.server['id'], body['instance_uuid'])
        self.assertEqual('create', body['action'])


class InstanceActionsV221TestJSON(base.BaseV2ComputeTest):
    """Test instance actions with compute microversion greater than 2.20"""

    create_default_network = True

    min_microversion = '2.21'
    max_microversion = 'latest'

    @classmethod
    def setup_clients(cls):
        super(InstanceActionsV221TestJSON, cls).setup_clients()
        cls.client = cls.servers_client

    @decorators.idempotent_id('0a0f85d4-10fa-41f6-bf80-a54fb4aa2ae1')
    def test_get_list_deleted_instance_actions(self):
        """Test listing actions for deleted instance

        Listing actions for deleted instance should succeed and the returned
        actions should contain 'create' and 'delete'.
        """
        server = self.create_test_server(wait_until='ACTIVE')
        self.client.delete_server(server['id'])
        waiters.wait_for_server_termination(self.client, server['id'])
        body = (self.client.list_instance_actions(server['id'])
                ['instanceActions'])
        self.assertEqual(len(body), 2, str(body))
        self.assertEqual(sorted([i['action'] for i in body]),
                         ['create', 'delete'])

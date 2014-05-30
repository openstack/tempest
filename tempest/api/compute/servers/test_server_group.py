# Copyright 2014 NEC Technologies India Ltd.
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
from tempest.common.utils import data_utils
from tempest import test


class ServerGroupTestJSON(base.BaseV2ComputeTest):
    """
    These tests check for the server-group APIs
    They create/delete server-groups with different policies.
    policies = affinity/anti-affinity
    It also adds the tests for list and get details of server-groups
    """
    @classmethod
    @test.safe_setup
    def setUpClass(cls):
        super(ServerGroupTestJSON, cls).setUpClass()
        if not test.is_extension_enabled('os-server-groups', 'compute'):
            msg = "os-server-groups extension is not enabled."
            raise cls.skipException(msg)
        cls.client = cls.servers_client
        server_group_name = data_utils.rand_name('server-group')
        cls.policy = ['affinity']

        _, cls.created_server_group = cls.create_test_server_group(
            server_group_name,
            cls.policy)

    def _create_server_group(self, name, policy):
        # create the test server-group with given policy
        server_group = {'name': name, 'policies': policy}
        resp, body = self.create_test_server_group(name, policy)
        self.assertEqual(200, resp.status)
        for key in ['name', 'policies']:
            self.assertEqual(server_group[key], body[key])
        return body

    def _delete_server_group(self, server_group):
        # delete the test server-group
        resp, _ = self.client.delete_server_group(server_group['id'])
        self.assertEqual(204, resp.status)
        # validation of server-group deletion
        resp, server_group_list = self.client.list_server_groups()
        self.assertEqual(200, resp.status)
        self.assertNotIn(server_group, server_group_list)

    def _create_delete_server_group(self, policy):
        # Create and Delete the server-group with given policy
        name = data_utils.rand_name('server-group')
        server_group = self._create_server_group(name, policy)
        self._delete_server_group(server_group)

    @test.attr(type='gate')
    def test_create_delete_server_group_with_affinity_policy(self):
        # Create and Delete the server-group with affinity policy
        self._create_delete_server_group(self.policy)

    @test.attr(type='gate')
    def test_create_delete_server_group_with_anti_affinity_policy(self):
        # Create and Delete the server-group with anti-affinity policy
        policy = ['anti-affinity']
        self._create_delete_server_group(policy)

    @test.skip_because(bug="1324348")
    @test.attr(type='gate')
    def test_create_delete_server_group_with_multiple_policies(self):
        # Create and Delete the server-group with multiple policies
        policies = ['affinity', 'affinity']
        self._create_delete_server_group(policies)

    @test.attr(type='gate')
    def test_create_delete_multiple_server_groups_with_same_name_policy(self):
        # Create and Delete the server-groups with same name and same policy
        server_groups = []
        server_group_name = data_utils.rand_name('server-group')
        for i in range(0, 2):
            server_groups.append(self._create_server_group(server_group_name,
                                                           self.policy))
        for key in ['name', 'policies']:
            self.assertEqual(server_groups[0][key], server_groups[1][key])
        self.assertNotEqual(server_groups[0]['id'], server_groups[1]['id'])

        for i in range(0, 2):
            self._delete_server_group(server_groups[i])

    @test.attr(type='gate')
    def test_get_server_group(self):
        # Get the server-group
        resp, body = self.client.get_server_group(
            self.created_server_group['id'])
        self.assertEqual(200, resp.status)
        self.assertEqual(self.created_server_group, body)

    @test.attr(type='gate')
    def test_list_server_groups(self):
        # List the server-group
        resp, body = self.client.list_server_groups()
        self.assertEqual(200, resp.status)
        self.assertIn(self.created_server_group, body)

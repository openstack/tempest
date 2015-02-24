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

from tempest_lib.common.utils import data_utils
from tempest_lib import decorators

from tempest.api.compute import base
from tempest import test


class ServerGroupTestJSON(base.BaseV2ComputeTest):
    """
    These tests check for the server-group APIs
    They create/delete server-groups with different policies.
    policies = affinity/anti-affinity
    It also adds the tests for list and get details of server-groups
    """
    @classmethod
    def skip_checks(cls):
        super(ServerGroupTestJSON, cls).skip_checks()
        if not test.is_extension_enabled('os-server-groups', 'compute'):
            msg = "os-server-groups extension is not enabled."
            raise cls.skipException(msg)

    @classmethod
    def setup_clients(cls):
        super(ServerGroupTestJSON, cls).setup_clients()
        cls.client = cls.servers_client

    @classmethod
    def resource_setup(cls):
        super(ServerGroupTestJSON, cls).resource_setup()
        server_group_name = data_utils.rand_name('server-group')
        cls.policy = ['affinity']

        cls.created_server_group = cls.create_test_server_group(
            server_group_name,
            cls.policy)

    def _create_server_group(self, name, policy):
        # create the test server-group with given policy
        server_group = {'name': name, 'policies': policy}
        body = self.create_test_server_group(name, policy)
        for key in ['name', 'policies']:
            self.assertEqual(server_group[key], body[key])
        return body

    def _delete_server_group(self, server_group):
        # delete the test server-group
        self.client.delete_server_group(server_group['id'])
        # validation of server-group deletion
        server_group_list = self.client.list_server_groups()
        self.assertNotIn(server_group, server_group_list)

    def _create_delete_server_group(self, policy):
        # Create and Delete the server-group with given policy
        name = data_utils.rand_name('server-group')
        server_group = self._create_server_group(name, policy)
        self._delete_server_group(server_group)

    @test.attr(type='gate')
    @test.idempotent_id('5dc57eda-35b7-4af7-9e5f-3c2be3d2d68b')
    def test_create_delete_server_group_with_affinity_policy(self):
        # Create and Delete the server-group with affinity policy
        self._create_delete_server_group(self.policy)

    @test.attr(type='gate')
    @test.idempotent_id('3645a102-372f-4140-afad-13698d850d23')
    def test_create_delete_server_group_with_anti_affinity_policy(self):
        # Create and Delete the server-group with anti-affinity policy
        policy = ['anti-affinity']
        self._create_delete_server_group(policy)

    @decorators.skip_because(bug="1324348")
    @test.attr(type='gate')
    @test.idempotent_id('6d9bae05-eb32-425d-a673-e14e1b1c6306')
    def test_create_delete_server_group_with_multiple_policies(self):
        # Create and Delete the server-group with multiple policies
        policies = ['affinity', 'affinity']
        self._create_delete_server_group(policies)

    @test.attr(type='gate')
    @test.idempotent_id('154dc5a4-a2fe-44b5-b99e-f15806a4a113')
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
    @test.idempotent_id('b3545034-dd78-48f0-bdc2-a4adfa6d0ead')
    def test_get_server_group(self):
        # Get the server-group
        body = self.client.get_server_group(
            self.created_server_group['id'])
        self.assertEqual(self.created_server_group, body)

    @test.attr(type='gate')
    @test.idempotent_id('d4874179-27b4-4d7d-80e4-6c560cdfe321')
    def test_list_server_groups(self):
        # List the server-group
        body = self.client.list_server_groups()
        self.assertIn(self.created_server_group, body)

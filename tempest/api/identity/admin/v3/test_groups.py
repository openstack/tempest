# Copyright 2013 IBM Corp.
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

from tempest.api.identity import base
from tempest.common.utils import data_utils
from tempest import test


class GroupsV3TestJSON(base.BaseIdentityV3AdminTest):

    @classmethod
    def resource_setup(cls):
        super(GroupsV3TestJSON, cls).resource_setup()
        cls.data.setup_test_domain()

    @test.idempotent_id('2e80343b-6c81-4ac3-88c7-452f3e9d5129')
    def test_group_create_update_get(self):
        name = data_utils.rand_name('Group')
        description = data_utils.rand_name('Description')
        group = self.groups_client.create_group(
            name=name, domain_id=self.data.domain['id'],
            description=description)['group']
        self.addCleanup(self.groups_client.delete_group, group['id'])
        self.assertEqual(group['name'], name)
        self.assertEqual(group['description'], description)

        new_name = data_utils.rand_name('UpdateGroup')
        new_desc = data_utils.rand_name('UpdateDescription')
        updated_group = self.groups_client.update_group(
            group['id'], name=new_name, description=new_desc)['group']
        self.assertEqual(updated_group['name'], new_name)
        self.assertEqual(updated_group['description'], new_desc)

        new_group = self.groups_client.show_group(group['id'])['group']
        self.assertEqual(group['id'], new_group['id'])
        self.assertEqual(new_name, new_group['name'])
        self.assertEqual(new_desc, new_group['description'])

    @test.idempotent_id('b66eb441-b08a-4a6d-81ab-fef71baeb26c')
    def test_group_update_with_few_fields(self):
        name = data_utils.rand_name('Group')
        old_description = data_utils.rand_name('Description')
        group = self.groups_client.create_group(
            name=name, domain_id=self.data.domain['id'],
            description=old_description)['group']
        self.addCleanup(self.groups_client.delete_group, group['id'])

        new_name = data_utils.rand_name('UpdateGroup')
        updated_group = self.groups_client.update_group(
            group['id'], name=new_name)['group']
        self.assertEqual(new_name, updated_group['name'])
        # Verify that 'description' is not being updated or deleted.
        self.assertEqual(old_description, updated_group['description'])

    @test.attr(type='smoke')
    @test.idempotent_id('1598521a-2f36-4606-8df9-30772bd51339')
    def test_group_users_add_list_delete(self):
        name = data_utils.rand_name('Group')
        group = self.groups_client.create_group(
            name=name, domain_id=self.data.domain['id'])['group']
        self.addCleanup(self.groups_client.delete_group, group['id'])
        # add user into group
        users = []
        for i in range(3):
            name = data_utils.rand_name('User')
            password = data_utils.rand_password()
            user = self.users_client.create_user(name, password)['user']
            users.append(user)
            self.addCleanup(self.users_client.delete_user, user['id'])
            self.groups_client.add_group_user(group['id'], user['id'])

        # list users in group
        group_users = self.groups_client.list_group_users(group['id'])['users']
        self.assertEqual(sorted(users), sorted(group_users))
        # check and delete user in group
        for user in users:
            self.groups_client.check_group_user_existence(
                group['id'], user['id'])
            self.groups_client.delete_group_user(group['id'], user['id'])
        group_users = self.groups_client.list_group_users(group['id'])['users']
        self.assertEqual(len(group_users), 0)

    @test.idempotent_id('64573281-d26a-4a52-b899-503cb0f4e4ec')
    def test_list_user_groups(self):
        # create a user
        user = self.users_client.create_user(
            data_utils.rand_name('User'), data_utils.rand_password())['user']
        self.addCleanup(self.users_client.delete_user, user['id'])
        # create two groups, and add user into them
        groups = []
        for i in range(2):
            name = data_utils.rand_name('Group')
            group = self.groups_client.create_group(
                name=name, domain_id=self.data.domain['id'])['group']
            groups.append(group)
            self.addCleanup(self.groups_client.delete_group, group['id'])
            self.groups_client.add_group_user(group['id'], user['id'])
        # list groups which user belongs to
        user_groups = self.users_client.list_user_groups(user['id'])['groups']
        self.assertEqual(sorted(groups), sorted(user_groups))
        self.assertEqual(2, len(user_groups))

    @test.idempotent_id('cc9a57a5-a9ed-4f2d-a29f-4f979a06ec71')
    def test_list_groups(self):
        # Test to list groups
        group_ids = list()
        fetched_ids = list()
        for _ in range(3):
            name = data_utils.rand_name('Group')
            description = data_utils.rand_name('Description')
            group = self.groups_client.create_group(
                name=name, domain_id=self.data.domain['id'],
                description=description)['group']
            self.addCleanup(self.groups_client.delete_group, group['id'])
            group_ids.append(group['id'])
        # List and Verify Groups
        body = self.groups_client.list_groups()['groups']
        for g in body:
            fetched_ids.append(g['id'])
        missing_groups = [g for g in group_ids if g not in fetched_ids]
        self.assertEqual([], missing_groups)

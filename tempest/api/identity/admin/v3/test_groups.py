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
    _interface = 'json'

    @classmethod
    def setUpClass(cls):
        super(GroupsV3TestJSON, cls).setUpClass()

    @test.attr(type='smoke')
    def test_group_create_update_get(self):
        name = data_utils.rand_name('Group')
        description = data_utils.rand_name('Description')
        resp, group = self.client.create_group(name,
                                               description=description)
        self.addCleanup(self.client.delete_group, group['id'])
        self.assertEqual(resp['status'], '201')
        self.assertEqual(group['name'], name)
        self.assertEqual(group['description'], description)

        new_name = data_utils.rand_name('UpdateGroup')
        new_desc = data_utils.rand_name('UpdateDescription')
        resp, updated_group = self.client.update_group(group['id'],
                                                       name=new_name,
                                                       description=new_desc)
        self.assertEqual(resp['status'], '200')
        self.assertEqual(updated_group['name'], new_name)
        self.assertEqual(updated_group['description'], new_desc)

        resp, new_group = self.client.get_group(group['id'])
        self.assertEqual(resp['status'], '200')
        self.assertEqual(group['id'], new_group['id'])
        self.assertEqual(new_name, new_group['name'])
        self.assertEqual(new_desc, new_group['description'])

    @test.attr(type='smoke')
    def test_group_users_add_list_delete(self):
        name = data_utils.rand_name('Group')
        resp, group = self.client.create_group(name)
        self.addCleanup(self.client.delete_group, group['id'])
        # add user into group
        users = []
        for i in range(3):
            name = data_utils.rand_name('User')
            resp, user = self.client.create_user(name)
            users.append(user)
            self.addCleanup(self.client.delete_user, user['id'])
            self.client.add_group_user(group['id'], user['id'])

        # list users in group
        resp, group_users = self.client.list_group_users(group['id'])
        self.assertEqual(resp['status'], '200')
        self.assertEqual(users.sort(), group_users.sort())
        # delete user in group
        for user in users:
            resp, body = self.client.delete_group_user(group['id'],
                                                       user['id'])
            self.assertEqual(resp['status'], '204')
        resp, group_users = self.client.list_group_users(group['id'])
        self.assertEqual(len(group_users), 0)


class GroupsV3TestXML(GroupsV3TestJSON):
    _interface = 'xml'

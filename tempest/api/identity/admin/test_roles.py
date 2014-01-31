# Copyright 2012 OpenStack Foundation
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
from tempest.test import attr


class RolesTestJSON(base.BaseIdentityV2AdminTest):
    _interface = 'json'

    @classmethod
    def setUpClass(cls):
        super(RolesTestJSON, cls).setUpClass()
        for _ in xrange(5):
            role_name = data_utils.rand_name(name='role-')
            resp, role = cls.client.create_role(role_name)
            cls.data.roles.append(role)

    def _get_role_params(self):
        self.data.setup_test_user()
        self.data.setup_test_role()
        user = self.get_user_by_name(self.data.test_user)
        tenant = self.get_tenant_by_name(self.data.test_tenant)
        role = self.get_role_by_name(self.data.test_role)
        return (user, tenant, role)

    def assert_role_in_role_list(self, role, roles):
        found = False
        for user_role in roles:
            if user_role['id'] == role['id']:
                found = True
        self.assertTrue(found, "assigned role was not in list")

    @attr(type='gate')
    def test_list_roles(self):
        # Return a list of all roles
        resp, body = self.client.list_roles()
        found = [role for role in body if role in self.data.roles]
        self.assertTrue(any(found))
        self.assertEqual(len(found), len(self.data.roles))

    @attr(type='gate')
    def test_role_create_delete(self):
        # Role should be created, verified, and deleted
        role_name = data_utils.rand_name(name='role-test-')
        resp, body = self.client.create_role(role_name)
        self.assertIn('status', resp)
        self.assertTrue(resp['status'].startswith('2'))
        self.assertEqual(role_name, body['name'])

        resp, body = self.client.list_roles()
        found = [role for role in body if role['name'] == role_name]
        self.assertTrue(any(found))

        resp, body = self.client.delete_role(found[0]['id'])
        self.assertIn('status', resp)
        self.assertTrue(resp['status'].startswith('2'))

        resp, body = self.client.list_roles()
        found = [role for role in body if role['name'] == role_name]
        self.assertFalse(any(found))

    @attr(type='gate')
    def test_assign_user_role(self):
        # Assign a role to a user on a tenant
        (user, tenant, role) = self._get_role_params()
        self.client.assign_user_role(tenant['id'], user['id'], role['id'])
        resp, roles = self.client.list_user_roles(tenant['id'], user['id'])
        self.assert_role_in_role_list(role, roles)

    @attr(type='gate')
    def test_remove_user_role(self):
        # Remove a role assigned to a user on a tenant
        (user, tenant, role) = self._get_role_params()
        resp, user_role = self.client.assign_user_role(tenant['id'],
                                                       user['id'], role['id'])
        resp, body = self.client.remove_user_role(tenant['id'], user['id'],
                                                  user_role['id'])
        self.assertEqual(resp['status'], '204')

    @attr(type='gate')
    def test_list_user_roles(self):
        # List roles assigned to a user on tenant
        (user, tenant, role) = self._get_role_params()
        self.client.assign_user_role(tenant['id'], user['id'], role['id'])
        resp, roles = self.client.list_user_roles(tenant['id'], user['id'])
        self.assert_role_in_role_list(role, roles)


class RolesTestXML(RolesTestJSON):
    _interface = 'xml'

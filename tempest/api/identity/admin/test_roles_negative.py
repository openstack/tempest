# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2013 Huawei Technologies Co.,LTD.
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

import uuid

from tempest.api.identity import base
from tempest.common.utils import data_utils
from tempest import exceptions
from tempest.test import attr


class RolesNegativeTestJSON(base.BaseIdentityAdminTest):
    _interface = 'json'

    def _get_role_params(self):
        self.data.setup_test_user()
        self.data.setup_test_role()
        user = self.get_user_by_name(self.data.test_user)
        tenant = self.get_tenant_by_name(self.data.test_tenant)
        role = self.get_role_by_name(self.data.test_role)
        return (user, tenant, role)

    @attr(type=['negative', 'gate'])
    def test_list_roles_by_unauthorized_user(self):
        # Non-administrator user should not be able to list roles
        self.assertRaises(exceptions.Unauthorized,
                          self.non_admin_client.list_roles)

    @attr(type=['negative', 'gate'])
    def test_list_roles_request_without_token(self):
        # Request to list roles without a valid token should fail
        token = self.client.get_auth()
        self.client.delete_token(token)
        self.assertRaises(exceptions.Unauthorized, self.client.list_roles)
        self.client.clear_auth()

    @attr(type=['negative', 'gate'])
    def test_role_create_blank_name(self):
        # Should not be able to create a role with a blank name
        self.assertRaises(exceptions.BadRequest, self.client.create_role, '')

    @attr(type=['negative', 'gate'])
    def test_create_role_by_unauthorized_user(self):
        # Non-administrator user should not be able to create role
        role_name = data_utils.rand_name(name='role-')
        self.assertRaises(exceptions.Unauthorized,
                          self.non_admin_client.create_role, role_name)

    @attr(type=['negative', 'gate'])
    def test_create_role_request_without_token(self):
        # Request to create role without a valid token should fail
        token = self.client.get_auth()
        self.client.delete_token(token)
        role_name = data_utils.rand_name(name='role-')
        self.assertRaises(exceptions.Unauthorized,
                          self.client.create_role, role_name)
        self.client.clear_auth()

    @attr(type=['negative', 'gate'])
    def test_role_create_duplicate(self):
        # Role names should be unique
        role_name = data_utils.rand_name(name='role-dup-')
        resp, body = self.client.create_role(role_name)
        role1_id = body.get('id')
        self.assertIn('status', resp)
        self.assertTrue(resp['status'].startswith('2'))
        self.addCleanup(self.client.delete_role, role1_id)
        self.assertRaises(exceptions.Conflict, self.client.create_role,
                          role_name)

    @attr(type=['negative', 'gate'])
    def test_delete_role_by_unauthorized_user(self):
        # Non-administrator user should not be able to delete role
        role_name = data_utils.rand_name(name='role-')
        resp, body = self.client.create_role(role_name)
        self.assertEqual(200, resp.status)
        self.data.roles.append(body)
        role_id = body.get('id')
        self.assertRaises(exceptions.Unauthorized,
                          self.non_admin_client.delete_role, role_id)

    @attr(type=['negative', 'gate'])
    def test_delete_role_request_without_token(self):
        # Request to delete role without a valid token should fail
        role_name = data_utils.rand_name(name='role-')
        resp, body = self.client.create_role(role_name)
        self.assertEqual(200, resp.status)
        self.data.roles.append(body)
        role_id = body.get('id')
        token = self.client.get_auth()
        self.client.delete_token(token)
        self.assertRaises(exceptions.Unauthorized,
                          self.client.delete_role,
                          role_id)
        self.client.clear_auth()

    @attr(type=['negative', 'gate'])
    def test_delete_role_non_existent(self):
        # Attempt to delete a non existent role should fail
        non_existent_role = str(uuid.uuid4().hex)
        self.assertRaises(exceptions.NotFound, self.client.delete_role,
                          non_existent_role)

    @attr(type=['negative', 'gate'])
    def test_assign_user_role_by_unauthorized_user(self):
        # Non-administrator user should not be authorized to
        # assign a role to user
        (user, tenant, role) = self._get_role_params()
        self.assertRaises(exceptions.Unauthorized,
                          self.non_admin_client.assign_user_role,
                          tenant['id'], user['id'], role['id'])

    @attr(type=['negative', 'gate'])
    def test_assign_user_role_request_without_token(self):
        # Request to assign a role to a user without a valid token
        (user, tenant, role) = self._get_role_params()
        token = self.client.get_auth()
        self.client.delete_token(token)
        self.assertRaises(exceptions.Unauthorized,
                          self.client.assign_user_role, tenant['id'],
                          user['id'], role['id'])
        self.client.clear_auth()

    @attr(type=['negative', 'gate'])
    def test_assign_user_role_for_non_existent_user(self):
        # Attempt to assign a role to a non existent user should fail
        (user, tenant, role) = self._get_role_params()
        non_existent_user = str(uuid.uuid4().hex)
        self.assertRaises(exceptions.NotFound, self.client.assign_user_role,
                          tenant['id'], non_existent_user, role['id'])

    @attr(type=['negative', 'gate'])
    def test_assign_user_role_for_non_existent_role(self):
        # Attempt to assign a non existent role to user should fail
        (user, tenant, role) = self._get_role_params()
        non_existent_role = str(uuid.uuid4().hex)
        self.assertRaises(exceptions.NotFound, self.client.assign_user_role,
                          tenant['id'], user['id'], non_existent_role)

    @attr(type=['negative', 'gate'])
    def test_assign_user_role_for_non_existent_tenant(self):
        # Attempt to assign a role on a non existent tenant should fail
        (user, tenant, role) = self._get_role_params()
        non_existent_tenant = str(uuid.uuid4().hex)
        self.assertRaises(exceptions.NotFound, self.client.assign_user_role,
                          non_existent_tenant, user['id'], role['id'])

    @attr(type=['negative', 'gate'])
    def test_assign_duplicate_user_role(self):
        # Duplicate user role should not get assigned
        (user, tenant, role) = self._get_role_params()
        self.client.assign_user_role(tenant['id'], user['id'], role['id'])
        self.assertRaises(exceptions.Conflict, self.client.assign_user_role,
                          tenant['id'], user['id'], role['id'])

    @attr(type=['negative', 'gate'])
    def test_remove_user_role_by_unauthorized_user(self):
        # Non-administrator user should not be authorized to
        # remove a user's role
        (user, tenant, role) = self._get_role_params()
        resp, user_role = self.client.assign_user_role(tenant['id'],
                                                       user['id'],
                                                       role['id'])
        self.assertRaises(exceptions.Unauthorized,
                          self.non_admin_client.remove_user_role,
                          tenant['id'], user['id'], role['id'])

    @attr(type=['negative', 'gate'])
    def test_remove_user_role_request_without_token(self):
        # Request to remove a user's role without a valid token
        (user, tenant, role) = self._get_role_params()
        resp, user_role = self.client.assign_user_role(tenant['id'],
                                                       user['id'],
                                                       role['id'])
        token = self.client.get_auth()
        self.client.delete_token(token)
        self.assertRaises(exceptions.Unauthorized,
                          self.client.remove_user_role, tenant['id'],
                          user['id'], role['id'])
        self.client.clear_auth()

    @attr(type=['negative', 'gate'])
    def test_remove_user_role_non_existant_user(self):
        # Attempt to remove a role from a non existent user should fail
        (user, tenant, role) = self._get_role_params()
        resp, user_role = self.client.assign_user_role(tenant['id'],
                                                       user['id'],
                                                       role['id'])
        non_existant_user = str(uuid.uuid4().hex)
        self.assertRaises(exceptions.NotFound, self.client.remove_user_role,
                          tenant['id'], non_existant_user, role['id'])

    @attr(type=['negative', 'gate'])
    def test_remove_user_role_non_existant_role(self):
        # Attempt to delete a non existent role from a user should fail
        (user, tenant, role) = self._get_role_params()
        resp, user_role = self.client.assign_user_role(tenant['id'],
                                                       user['id'],
                                                       role['id'])
        non_existant_role = str(uuid.uuid4().hex)
        self.assertRaises(exceptions.NotFound, self.client.remove_user_role,
                          tenant['id'], user['id'], non_existant_role)

    @attr(type=['negative', 'gate'])
    def test_remove_user_role_non_existant_tenant(self):
        # Attempt to remove a role from a non existent tenant should fail
        (user, tenant, role) = self._get_role_params()
        resp, user_role = self.client.assign_user_role(tenant['id'],
                                                       user['id'],
                                                       role['id'])
        non_existant_tenant = str(uuid.uuid4().hex)
        self.assertRaises(exceptions.NotFound, self.client.remove_user_role,
                          non_existant_tenant, user['id'], role['id'])

    @attr(type=['negative', 'gate'])
    def test_list_user_roles_by_unauthorized_user(self):
        # Non-administrator user should not be authorized to list
        # a user's roles
        (user, tenant, role) = self._get_role_params()
        self.client.assign_user_role(tenant['id'], user['id'], role['id'])
        self.assertRaises(exceptions.Unauthorized,
                          self.non_admin_client.list_user_roles, tenant['id'],
                          user['id'])

    @attr(type=['negative', 'gate'])
    def test_list_user_roles_request_without_token(self):
        # Request to list user's roles without a valid token should fail
        (user, tenant, role) = self._get_role_params()
        token = self.client.get_auth()
        self.client.delete_token(token)
        try:
            self.assertRaises(exceptions.Unauthorized,
                              self.client.list_user_roles, tenant['id'],
                              user['id'])
        finally:
            self.client.clear_auth()

    @attr(type=['negative', 'gate'])
    def test_list_user_roles_for_non_existent_user(self):
        # Attempt to list roles of a non existent user should fail
        (user, tenant, role) = self._get_role_params()
        non_existent_user = str(uuid.uuid4().hex)
        self.assertRaises(exceptions.NotFound, self.client.list_user_roles,
                          tenant['id'], non_existent_user)


class RolesTestXML(RolesNegativeTestJSON):
    _interface = 'xml'

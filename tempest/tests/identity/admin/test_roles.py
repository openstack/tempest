# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2012 OpenStack, LLC
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

import unittest2 as unittest

from tempest import exceptions
from tempest.common.utils.data_utils import rand_name
from tempest.tests.identity.base import BaseIdentityAdminTest


class RolesTest(BaseIdentityAdminTest):

    @classmethod
    def setUpClass(cls):
        super(RolesTest, cls).setUpClass()

        for _ in xrange(5):
            resp, role = cls.client.create_role(rand_name('role-'))
            cls.data.roles.append(role)

    def _get_role_params(self):
        self.data.setup_test_user()
        self.data.setup_test_role()
        user = self.get_user_by_name(self.data.test_user)
        tenant = self.get_tenant_by_name(self.data.test_tenant)
        role = self.get_role_by_name(self.data.test_role)
        return (user, tenant, role)

    def test_list_roles(self):
        """Return a list of all roles"""
        resp, body = self.client.list_roles()
        found = [role for role in body if role in self.data.roles]
        self.assertTrue(any(found))
        self.assertEqual(len(found), len(self.data.roles))

    def test_list_roles_by_unauthorized_user(self):
        """Non admin user should not be able to list roles"""
        self.assertRaises(exceptions.Unauthorized,
                self.non_admin_client.list_roles)

    def test_list_roles_request_without_token(self):
        """Request to list roles without a valid token should fail"""
        token = self.client.get_auth()
        self.client.delete_token(token)
        self.assertRaises(exceptions.Unauthorized, self.client.list_roles)
        self.client.clear_auth()

    def test_role_create_delete(self):
        """Role should be created, verified, and deleted"""
        role_name = rand_name('role-test-')
        resp, body = self.client.create_role(role_name)
        self.assertTrue('status' in resp)
        self.assertTrue(resp['status'].startswith('2'))
        self.assertEqual(role_name, body['name'])

        resp, body = self.client.list_roles()
        found = [role for role in body if role['name'] == role_name]
        self.assertTrue(any(found))

        resp, body = self.client.delete_role(found[0]['id'])
        self.assertTrue('status' in resp)
        self.assertTrue(resp['status'].startswith('2'))

        resp, body = self.client.list_roles()
        found = [role for role in body if role['name'] == role_name]
        self.assertFalse(any(found))

    def test_role_create_blank_name(self):
        """Should not be able to create a role with a blank name"""
        self.assertRaises(exceptions.BadRequest, self.client.create_role, '')

    def test_role_create_duplicate(self):
        """Role names should be unique"""
        role_name = rand_name('role-dup-')
        resp, body = self.client.create_role(role_name)
        role1_id = body.get('id')
        self.assertTrue('status' in resp)
        self.assertTrue(resp['status'].startswith('2'))

        try:
            resp, body = self.client.create_role(role_name)
            # this should raise an exception
            self.fail('Should not be able to create a duplicate role name.'
                      ' %s' % role_name)
        except exceptions.Duplicate:
            pass
        self.client.delete_role(role1_id)


class UserRolesTest(RolesTest):

    @classmethod
    def setUpClass(cls):
        super(UserRolesTest, cls).setUpClass()

    def test_assign_user_role(self):
        """Assign a role to a user on a tenant"""
        (user, tenant, role) = self._get_role_params()
        self.client.assign_user_role(tenant['id'], user['id'], role['id'])
        resp, roles = self.client.list_user_roles(tenant['id'], user['id'])
        self.assertEquals(1, len(roles))
        self.assertEquals(roles[0]['id'], role['id'])

    def test_assign_user_role_by_unauthorized_user(self):
        """Non admin user should not be authorized to assign a role to user"""
        (user, tenant, role) = self._get_role_params()
        self.assertRaises(exceptions.Unauthorized,
                          self.non_admin_client.assign_user_role,
                          tenant['id'], user['id'], role['id'])

    def test_assign_user_role_request_without_token(self):
        """Request to assign a role to a user without a valid token"""
        (user, tenant, role) = self._get_role_params()
        token = self.client.get_auth()
        self.client.delete_token(token)
        self.assertRaises(exceptions.Unauthorized,
                          self.client.assign_user_role, tenant['id'],
                          user['id'], role['id'])
        self.client.clear_auth()

    def test_assign_user_role_for_non_existent_user(self):
        """Attempt to assign a role to a non existent user should fail"""
        (user, tenant, role) = self._get_role_params()
        self.assertRaises(exceptions.NotFound, self.client.assign_user_role,
                         tenant['id'], 'junk-user-id-999', role['id'])

    def test_assign_user_role_for_non_existent_role(self):
        """Attempt to assign a non existent role to user should fail"""
        (user, tenant, role) = self._get_role_params()
        self.assertRaises(exceptions.NotFound, self.client.assign_user_role,
                         tenant['id'], user['id'], 'junk-role-id-12345')

    def test_assign_user_role_for_non_existent_tenant(self):
        """Attempt to assign a role on a non existent tenant should fail"""
        (user, tenant, role) = self._get_role_params()
        self.assertRaises(exceptions.NotFound, self.client.assign_user_role,
                         'junk-tenant-1234', user['id'], role['id'])

    def test_assign_duplicate_user_role(self):
        """Duplicate user role should not get assigned"""
        (user, tenant, role) = self._get_role_params()
        self.client.assign_user_role(tenant['id'], user['id'], role['id'])
        self.assertRaises(exceptions.Duplicate, self.client.assign_user_role,
                          tenant['id'], user['id'], role['id'])

    def test_remove_user_role(self):
        """Remove a role assigned to a user on a tenant"""
        (user, tenant, role) = self._get_role_params()
        resp, user_role = self.client.assign_user_role(tenant['id'],
                                                       user['id'], role['id'])
        resp, body = self.client.remove_user_role(tenant['id'], user['id'],
                                                  user_role['id'])
        self.assertEquals(resp['status'], '204')

    def test_remove_user_role_by_unauthorized_user(self):
        """Non admin user should not be authorized to remove a user's role"""
        (user, tenant, role) = self._get_role_params()
        resp, user_role = self.client.assign_user_role(tenant['id'],
                                                       user['id'],
                                                       role['id'])
        self.assertRaises(exceptions.Unauthorized,
                         self.non_admin_client.remove_user_role,
                         tenant['id'], user['id'], role['id'])

    def test_remove_user_role_request_without_token(self):
        """Request to remove a user's role without a valid token"""
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

    def test_remove_user_role_non_existant_user(self):
        """Attempt to remove a role from a non existent user should fail"""
        (user, tenant, role) = self._get_role_params()
        resp, user_role = self.client.assign_user_role(tenant['id'],
                                                       user['id'],
                                                       role['id'])
        self.assertRaises(exceptions.NotFound, self.client.remove_user_role,
                         tenant['id'], 'junk-user-id-123', role['id'])

    def test_remove_user_role_non_existant_role(self):
        """Attempt to delete a non existent role from a user should fail"""
        (user, tenant, role) = self._get_role_params()
        resp, user_role = self.client.assign_user_role(tenant['id'],
                                                       user['id'],
                                                       role['id'])
        self.assertRaises(exceptions.NotFound, self.client.remove_user_role,
                          tenant['id'], user['id'], 'junk-user-role-123')

    def test_remove_user_role_non_existant_tenant(self):
        """Attempt to remove a role from a non existent tenant should fail"""
        (user, tenant, role) = self._get_role_params()
        resp, user_role = self.client.assign_user_role(tenant['id'],
                                                       user['id'],
                                                       role['id'])
        self.assertRaises(exceptions.NotFound, self.client.remove_user_role,
                          'junk-tenant-id-123', user['id'], role['id'])

    def test_list_user_roles(self):
        """List roles assigned to a user on tenant"""
        (user, tenant, role) = self._get_role_params()
        self.client.assign_user_role(tenant['id'], user['id'], role['id'])
        resp, roles = self.client.list_user_roles(tenant['id'], user['id'])
        self.assertEquals(1, len(roles))
        self.assertEquals(role['id'], roles[0]['id'])

    def test_list_user_roles_by_unauthorized_user(self):
        """Non admin user should not be authorized to list a user's roles"""
        (user, tenant, role) = self._get_role_params()
        self.client.assign_user_role(tenant['id'], user['id'], role['id'])
        self.assertRaises(exceptions.Unauthorized,
                          self.non_admin_client.list_user_roles, tenant['id'],
                          user['id'])

    def test_list_user_roles_request_without_token(self):
        """Request to list user's roles without a valid token should fail"""
        (user, tenant, role) = self._get_role_params()
        token = self.client.get_auth()
        self.client.delete_token(token)
        self.assertRaises(exceptions.Unauthorized,
                          self.client.list_user_roles, tenant['id'],
                          user['id'])
        self.client.clear_auth()

    def test_list_user_roles_for_non_existent_user(self):
        """Attempt to list roles of a non existent user should fail"""
        (user, tenant, role) = self._get_role_params()
        self.assertRaises(exceptions.NotFound, self.client.list_user_roles,
        tenant['id'], 'junk-role-aabbcc11')

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

import nose
import unittest2 as unittest

from tempest import clients
from tempest.common.utils.data_utils import rand_name


class BaseIdAdminTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        os = clients.IdentityManager(interface=cls._interface)
        cls.client = os.admin_client
        cls.token_client = os.token_client

        if not cls.client.has_admin_extensions():
            raise nose.SkipTest("Admin extensions disabled")

        cls.data = DataGenerator(cls.client)

        os = clients.IdentityNaManager(interface=cls._interface)
        cls.non_admin_client = os.admin_client

    @classmethod
    def tearDownClass(cls):
        cls.data.teardown_all()

    def disable_user(self, user_name):
        user = self.get_user_by_name(user_name)
        self.client.enable_disable_user(user['id'], False)

    def disable_tenant(self, tenant_name):
        tenant = self.get_tenant_by_name(tenant_name)
        self.client.update_tenant(tenant['id'], tenant['description'], False)

    def get_user_by_name(self, name):
        _, users = self.client.get_users()
        user = [u for u in users if u['name'] == name]
        if len(user) > 0:
            return user[0]

    def get_tenant_by_name(self, name):
        _, tenants = self.client.list_tenants()
        tenant = [t for t in tenants if t['name'] == name]
        if len(tenant) > 0:
            return tenant[0]

    def get_role_by_name(self, name):
        _, roles = self.client.list_roles()
        role = [r for r in roles if r['name'] == name]
        if len(role) > 0:
            return role[0]


class BaseIdentityAdminTestJSON(BaseIdAdminTest):
    @classmethod
    def setUpClass(cls):
        cls._interface = "json"
        super(BaseIdentityAdminTestJSON, cls).setUpClass()

BaseIdentityAdminTest = BaseIdentityAdminTestJSON


class BaseIdentityAdminTestXML(BaseIdAdminTest):
    @classmethod
    def setUpClass(cls):
        cls._interface = "xml"
        super(BaseIdentityAdminTestXML, cls).setUpClass()


class DataGenerator(object):

        def __init__(self, client):
            self.client = client
            self.users = []
            self.tenants = []
            self.roles = []
            self.role_name = None

        def setup_test_user(self):
            """Set up a test user."""
            self.setup_test_tenant()
            self.test_user = rand_name('test_user_')
            self.test_password = rand_name('pass_')
            self.test_email = self.test_user + '@testmail.tm'
            resp, self.user = self.client.create_user(self.test_user,
                                                      self.test_password,
                                                      self.tenant['id'],
                                                      self.test_email)
            self.users.append(self.user)

        def setup_test_tenant(self):
            """Set up a test tenant."""
            self.test_tenant = rand_name('test_tenant_')
            self.test_description = rand_name('desc_')
            resp, self.tenant = self.client.create_tenant(
                name=self.test_tenant,
                description=self.test_description)
            self.tenants.append(self.tenant)

        def setup_test_role(self):
            """Set up a test role."""
            self.test_role = rand_name('role')
            resp, self.role = self.client.create_role(self.test_role)
            self.roles.append(self.role)

        def teardown_all(self):
            for user in self.users:
                self.client.delete_user(user['id'])
            for tenant in self.tenants:
                self.client.delete_tenant(tenant['id'])
            for role in self.roles:
                self.client.delete_role(role['id'])

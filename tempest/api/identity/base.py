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


from tempest import clients
from tempest.common.utils.data_utils import rand_name
import tempest.test


class BaseIdentityAdminTest(tempest.test.BaseTestCase):

    @classmethod
    def setUpClass(cls):
        super(BaseIdentityAdminTest, cls).setUpClass()
        os = clients.AdminManager(interface=cls._interface)
        cls.client = os.identity_client
        cls.token_client = os.token_client
        cls.endpoints_client = os.endpoints_client
        cls.v3_client = os.identity_v3_client
        cls.service_client = os.service_client
        cls.policy_client = os.policy_client
        cls.v3_token = os.token_v3_client
        cls.creds_client = os.credentials_client

        if not cls.client.has_admin_extensions():
            raise cls.skipException("Admin extensions disabled")

        cls.data = DataGenerator(cls.client)
        cls.v3data = DataGenerator(cls.v3_client)

        os = clients.Manager(interface=cls._interface)
        cls.non_admin_client = os.identity_client
        cls.v3_non_admin_client = os.identity_v3_client

    @classmethod
    def tearDownClass(cls):
        cls.data.teardown_all()
        cls.v3data.teardown_all()
        super(BaseIdentityAdminTest, cls).tearDownClass()

    def disable_user(self, user_name):
        user = self.get_user_by_name(user_name)
        self.client.enable_disable_user(user['id'], False)

    def disable_tenant(self, tenant_name):
        tenant = self.get_tenant_by_name(tenant_name)
        self.client.update_tenant(tenant['id'], enabled=False)

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


class DataGenerator(object):

        def __init__(self, client):
            self.client = client
            self.users = []
            self.tenants = []
            self.roles = []
            self.role_name = None
            self.v3_users = []
            self.projects = []
            self.v3_roles = []

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

        def setup_test_v3_user(self):
            """Set up a test v3 user."""
            self.setup_test_project()
            self.test_user = rand_name('test_user_')
            self.test_password = rand_name('pass_')
            self.test_email = self.test_user + '@testmail.tm'
            resp, self.v3_user = self.client.create_user(self.test_user,
                                                         self.test_password,
                                                         self.project['id'],
                                                         self.test_email)
            self.v3_users.append(self.v3_user)

        def setup_test_project(self):
            """Set up a test project."""
            self.test_project = rand_name('test_project_')
            self.test_description = rand_name('desc_')
            resp, self.project = self.client.create_project(
                name=self.test_project,
                description=self.test_description)
            self.projects.append(self.project)

        def setup_test_v3_role(self):
            """Set up a test v3 role."""
            self.test_role = rand_name('role')
            resp, self.v3_role = self.client.create_role(self.test_role)
            self.v3_roles.append(self.v3_role)

        def teardown_all(self):
            for user in self.users:
                self.client.delete_user(user['id'])
            for tenant in self.tenants:
                self.client.delete_tenant(tenant['id'])
            for role in self.roles:
                self.client.delete_role(role['id'])
            for v3_user in self.v3_users:
                self.client.delete_user(v3_user['id'])
            for v3_project in self.projects:
                self.client.delete_project(v3_project['id'])
            for v3_role in self.v3_roles:
                self.client.delete_role(v3_role['id'])

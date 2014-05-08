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


from tempest import auth
from tempest import clients
from tempest.common.utils import data_utils
from tempest import config
import tempest.test

CONF = config.CONF


class BaseIdentityAdminTest(tempest.test.BaseTestCase):

    @classmethod
    def setUpClass(cls):
        super(BaseIdentityAdminTest, cls).setUpClass()
        cls.os_adm = clients.AdminManager(interface=cls._interface)
        cls.os = clients.Manager(interface=cls._interface)

    @classmethod
    def disable_user(cls, user_name):
        user = cls.get_user_by_name(user_name)
        cls.client.enable_disable_user(user['id'], False)

    @classmethod
    def disable_tenant(cls, tenant_name):
        tenant = cls.get_tenant_by_name(tenant_name)
        cls.client.update_tenant(tenant['id'], enabled=False)

    @classmethod
    def get_user_by_name(cls, name):
        _, users = cls.client.get_users()
        user = [u for u in users if u['name'] == name]
        if len(user) > 0:
            return user[0]

    @classmethod
    def get_tenant_by_name(cls, name):
        try:
            _, tenants = cls.client.list_tenants()
        except AttributeError:
            _, tenants = cls.client.list_projects()
        tenant = [t for t in tenants if t['name'] == name]
        if len(tenant) > 0:
            return tenant[0]

    @classmethod
    def get_role_by_name(cls, name):
        _, roles = cls.client.list_roles()
        role = [r for r in roles if r['name'] == name]
        if len(role) > 0:
            return role[0]


class BaseIdentityV2AdminTest(BaseIdentityAdminTest):

    @classmethod
    def setUpClass(cls):
        if not CONF.identity_feature_enabled.api_v2:
            raise cls.skipException("Identity api v2 is not enabled")
        super(BaseIdentityV2AdminTest, cls).setUpClass()
        cls.client = cls.os_adm.identity_client
        cls.token_client = cls.os_adm.token_client
        if not cls.client.has_admin_extensions():
            raise cls.skipException("Admin extensions disabled")
        cls.data = DataGenerator(cls.client)
        cls.non_admin_client = cls.os.identity_client

    @classmethod
    def tearDownClass(cls):
        cls.data.teardown_all()
        super(BaseIdentityV2AdminTest, cls).tearDownClass()


class BaseIdentityV3AdminTest(BaseIdentityAdminTest):

    @classmethod
    def setUpClass(cls):
        if not CONF.identity_feature_enabled.api_v3:
            raise cls.skipException("Identity api v3 is not enabled")
        super(BaseIdentityV3AdminTest, cls).setUpClass()
        cls.client = cls.os_adm.identity_v3_client
        cls.token = cls.os_adm.token_v3_client
        cls.endpoints_client = cls.os_adm.endpoints_client
        cls.data = DataGenerator(cls.client)
        cls.non_admin_client = cls.os.identity_v3_client
        cls.service_client = cls.os_adm.service_client
        cls.policy_client = cls.os_adm.policy_client
        cls.creds_client = cls.os_adm.credentials_client
        cls.non_admin_client = cls.os.identity_v3_client

    @classmethod
    def tearDownClass(cls):
        cls.data.teardown_all()
        super(BaseIdentityV3AdminTest, cls).tearDownClass()


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

        @property
        def test_credentials(self):
            return auth.get_credentials(username=self.test_user,
                                        user_id=self.user['id'],
                                        password=self.test_password,
                                        tenant_name=self.test_tenant,
                                        tenant_id=self.tenant['id'])

        def setup_test_user(self):
            """Set up a test user."""
            self.setup_test_tenant()
            self.test_user = data_utils.rand_name('test_user_')
            self.test_password = data_utils.rand_name('pass_')
            self.test_email = self.test_user + '@testmail.tm'
            resp, self.user = self.client.create_user(self.test_user,
                                                      self.test_password,
                                                      self.tenant['id'],
                                                      self.test_email)
            self.users.append(self.user)

        def setup_test_tenant(self):
            """Set up a test tenant."""
            self.test_tenant = data_utils.rand_name('test_tenant_')
            self.test_description = data_utils.rand_name('desc_')
            resp, self.tenant = self.client.create_tenant(
                name=self.test_tenant,
                description=self.test_description)
            self.tenants.append(self.tenant)

        def setup_test_role(self):
            """Set up a test role."""
            self.test_role = data_utils.rand_name('role')
            resp, self.role = self.client.create_role(self.test_role)
            self.roles.append(self.role)

        def setup_test_v3_user(self):
            """Set up a test v3 user."""
            self.setup_test_project()
            self.test_user = data_utils.rand_name('test_user_')
            self.test_password = data_utils.rand_name('pass_')
            self.test_email = self.test_user + '@testmail.tm'
            resp, self.v3_user = self.client.create_user(
                self.test_user,
                password=self.test_password,
                project_id=self.project['id'],
                email=self.test_email)
            self.v3_users.append(self.v3_user)

        def setup_test_project(self):
            """Set up a test project."""
            self.test_project = data_utils.rand_name('test_project_')
            self.test_description = data_utils.rand_name('desc_')
            resp, self.project = self.client.create_project(
                name=self.test_project,
                description=self.test_description)
            self.projects.append(self.project)

        def setup_test_v3_role(self):
            """Set up a test v3 role."""
            self.test_role = data_utils.rand_name('role')
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

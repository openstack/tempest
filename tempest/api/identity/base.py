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

from tempest.common.utils import data_utils
from tempest import config
import tempest.test

CONF = config.CONF


class BaseIdentityTest(tempest.test.BaseTestCase):

    @classmethod
    def disable_user(cls, user_name):
        user = cls.get_user_by_name(user_name)
        cls.users_client.update_user_enabled(user['id'], enabled=False)

    @classmethod
    def disable_tenant(cls, tenant_name):
        tenant = cls.get_tenant_by_name(tenant_name)
        cls.tenants_client.update_tenant(tenant['id'], enabled=False)

    @classmethod
    def get_user_by_name(cls, name, domain_id=None):
        if domain_id:
            params = {'domain_id': domain_id}
            users = cls.users_client.list_users(**params)['users']
        else:
            users = cls.users_client.list_users()['users']
        user = [u for u in users if u['name'] == name]
        if len(user) > 0:
            return user[0]

    @classmethod
    def get_tenant_by_name(cls, name):
        try:
            tenants = cls.tenants_client.list_tenants()['tenants']
        except AttributeError:
            tenants = cls.projects_client.list_projects()['projects']
        tenant = [t for t in tenants if t['name'] == name]
        if len(tenant) > 0:
            return tenant[0]

    @classmethod
    def get_role_by_name(cls, name):
        roles = cls.roles_client.list_roles()['roles']
        role = [r for r in roles if r['name'] == name]
        if len(role) > 0:
            return role[0]

    def _create_test_user(self, **kwargs):
        if kwargs['password'] is None:
            user_password = data_utils.rand_password()
            kwargs['password'] = user_password
        user = self.users_client.create_user(**kwargs)['user']
        # Delete the user at the end of the test
        self.addCleanup(self.users_client.delete_user, user['id'])
        return user

    def setup_test_role(self):
        """Set up a test role."""
        role = self.roles_client.create_role(
            name=data_utils.rand_name('test_role'))['role']
        # Delete the role at the end of the test
        self.addCleanup(self.roles_client.delete_role, role['id'])
        return role


class BaseIdentityV2Test(BaseIdentityTest):

    credentials = ['primary']

    # identity v2 tests should obtain tokens and create accounts via v2
    # regardless of the configured CONF.identity.auth_version
    identity_version = 'v2'

    @classmethod
    def setup_clients(cls):
        super(BaseIdentityV2Test, cls).setup_clients()
        cls.non_admin_client = cls.os.identity_public_client
        cls.non_admin_token_client = cls.os.token_client
        cls.non_admin_tenants_client = cls.os.tenants_public_client
        cls.non_admin_users_client = cls.os.users_public_client


class BaseIdentityV2AdminTest(BaseIdentityV2Test):

    credentials = ['primary', 'admin']

    @classmethod
    def setup_clients(cls):
        super(BaseIdentityV2AdminTest, cls).setup_clients()
        cls.client = cls.os_adm.identity_client
        cls.non_admin_client = cls.os.identity_client
        cls.token_client = cls.os_adm.token_client
        cls.tenants_client = cls.os_adm.tenants_client
        cls.non_admin_tenants_client = cls.os.tenants_client
        cls.roles_client = cls.os_adm.roles_client
        cls.non_admin_roles_client = cls.os.roles_client
        cls.users_client = cls.os_adm.users_client
        cls.non_admin_users_client = cls.os.users_client
        cls.services_client = cls.os_adm.identity_services_client
        cls.endpoints_client = cls.os_adm.endpoints_client

    @classmethod
    def resource_setup(cls):
        super(BaseIdentityV2AdminTest, cls).resource_setup()
        cls.projects_client = cls.tenants_client

    def setup_test_user(self, password=None):
        """Set up a test user."""
        tenant = self.setup_test_tenant()
        username = data_utils.rand_name('test_user')
        email = username + '@testmail.tm'
        user = self._create_test_user(name=username, email=email,
                                      tenantId=tenant['id'], password=password)
        return user

    def setup_test_tenant(self):
        """Set up a test tenant."""
        tenant = self.projects_client.create_tenant(
            name=data_utils.rand_name('test_tenant'),
            description=data_utils.rand_name('desc'))['tenant']
        # Delete the tenant at the end of the test
        self.addCleanup(self.tenants_client.delete_tenant, tenant['id'])
        return tenant


class BaseIdentityV3Test(BaseIdentityTest):

    credentials = ['primary']

    # identity v3 tests should obtain tokens and create accounts via v3
    # regardless of the configured CONF.identity.auth_version
    identity_version = 'v3'

    @classmethod
    def setup_clients(cls):
        super(BaseIdentityV3Test, cls).setup_clients()
        cls.non_admin_client = cls.os.identity_v3_client
        cls.non_admin_users_client = cls.os.users_v3_client
        cls.non_admin_token = cls.os.token_v3_client
        cls.non_admin_projects_client = cls.os.projects_client


class BaseIdentityV3AdminTest(BaseIdentityV3Test):

    credentials = ['primary', 'admin']

    @classmethod
    def setup_clients(cls):
        super(BaseIdentityV3AdminTest, cls).setup_clients()
        cls.client = cls.os_adm.identity_v3_client
        cls.domains_client = cls.os_adm.domains_client
        cls.users_client = cls.os_adm.users_v3_client
        cls.trusts_client = cls.os_adm.trusts_client
        cls.roles_client = cls.os_adm.roles_v3_client
        cls.token = cls.os_adm.token_v3_client
        cls.endpoints_client = cls.os_adm.endpoints_v3_client
        cls.regions_client = cls.os_adm.regions_client
        cls.services_client = cls.os_adm.identity_services_v3_client
        cls.policies_client = cls.os_adm.policies_client
        cls.creds_client = cls.os_adm.credentials_client
        cls.groups_client = cls.os_adm.groups_client
        cls.projects_client = cls.os_adm.projects_client
        if CONF.identity.admin_domain_scope:
            # NOTE(andreaf) When keystone policy requires it, the identity
            # admin clients for these tests shall use 'domain' scoped tokens.
            # As the client manager is already created by the base class,
            # we set the scope for the inner auth provider.
            cls.os_adm.auth_provider.scope = 'domain'

    @classmethod
    def disable_user(cls, user_name, domain_id=None):
        user = cls.get_user_by_name(user_name, domain_id)
        cls.users_client.update_user(user['id'], name=user_name, enabled=False)

    @classmethod
    def create_domain(cls):
        """Create a domain."""
        domain = cls.domains_client.create_domain(
            name=data_utils.rand_name('test_domain'),
            description=data_utils.rand_name('desc'))['domain']
        return domain

    def delete_domain(self, domain_id):
        # NOTE(mpavlase) It is necessary to disable the domain before deleting
        # otherwise it raises Forbidden exception
        self.domains_client.update_domain(domain_id, enabled=False)
        self.domains_client.delete_domain(domain_id)

    def setup_test_user(self, password=None):
        """Set up a test user."""
        project = self.setup_test_project()
        username = data_utils.rand_name('test_user')
        email = username + '@testmail.tm'
        user = self._create_test_user(name=username, email=email,
                                      project_id=project['id'],
                                      password=password)
        return user

    def setup_test_project(self):
        """Set up a test project."""
        project = self.projects_client.create_project(
            name=data_utils.rand_name('test_project'),
            description=data_utils.rand_name('desc'))['project']
        # Delete the project at the end of the test
        self.addCleanup(self.projects_client.delete_project, project['id'])
        return project

    def setup_test_domain(self):
        """Set up a test domain."""
        domain = self.create_domain()
        # Delete the domain at the end of the test
        self.addCleanup(self.delete_domain, domain['id'])
        return domain

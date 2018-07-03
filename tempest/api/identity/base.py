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

from tempest import config
from tempest.lib.common.utils import data_utils
from tempest.lib.common.utils import test_utils
import tempest.test

CONF = config.CONF


class BaseIdentityTest(tempest.test.BaseTestCase):

    @classmethod
    def setup_credentials(cls):
        # Create no network resources for these test.
        cls.set_network_resources()
        super(BaseIdentityTest, cls).setup_credentials()

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
        if user:
            return user[0]

    @classmethod
    def get_tenant_by_name(cls, name):
        try:
            tenants = cls.tenants_client.list_tenants()['tenants']
        except AttributeError:
            tenants = cls.projects_client.list_projects()['projects']
        tenant = [t for t in tenants if t['name'] == name]
        if tenant:
            return tenant[0]

    @classmethod
    def get_role_by_name(cls, name):
        roles = cls.roles_client.list_roles()['roles']
        role = [r for r in roles if r['name'] == name]
        if role:
            return role[0]

    def create_test_user(self, **kwargs):
        if kwargs.get('password', None) is None:
            kwargs['password'] = data_utils.rand_password()
        if 'name' not in kwargs:
            kwargs['name'] = data_utils.rand_name('test_user')
        if 'email' not in kwargs:
            kwargs['email'] = kwargs['name'] + '@testmail.tm'

        user = self.users_client.create_user(**kwargs)['user']
        # Delete the user at the end of the test
        self.addCleanup(
            test_utils.call_and_ignore_notfound_exc,
            self.users_client.delete_user, user['id'])
        return user

    def setup_test_role(self, name=None, domain_id=None):
        """Set up a test role."""
        params = {'name': name or data_utils.rand_name('test_role')}
        if domain_id:
            params['domain_id'] = domain_id

        role = self.roles_client.create_role(**params)['role']
        # Delete the role at the end of the test
        self.addCleanup(
            test_utils.call_and_ignore_notfound_exc,
            self.roles_client.delete_role, role['id'])
        return role


class BaseIdentityV2Test(BaseIdentityTest):

    credentials = ['primary']

    # identity v2 tests should obtain tokens and create accounts via v2
    # regardless of the configured CONF.identity.auth_version
    identity_version = 'v2'

    @classmethod
    def setup_clients(cls):
        super(BaseIdentityV2Test, cls).setup_clients()
        cls.non_admin_client = cls.os_primary.identity_public_client
        cls.non_admin_token_client = cls.os_primary.token_client
        cls.non_admin_tenants_client = cls.os_primary.tenants_public_client
        cls.non_admin_users_client = cls.os_primary.users_public_client


class BaseIdentityV2AdminTest(BaseIdentityV2Test):

    credentials = ['primary', 'admin']

    # NOTE(andreaf) Identity tests work with credentials, so it is safer
    # for them to always use disposable credentials. Forcing dynamic creds
    # on regular identity tests would be however to restrictive, since it
    # would prevent any identity test from being executed against clouds where
    # admin credentials are not available.
    # Since All admin tests require admin credentials to be
    # executed, so this will not impact the ability to execute tests.
    force_tenant_isolation = True

    @classmethod
    def skip_checks(cls):
        super(BaseIdentityV2AdminTest, cls).skip_checks()
        if not CONF.identity_feature_enabled.api_v2_admin:
            raise cls.skipException('Identity v2 admin not available')

    @classmethod
    def setup_clients(cls):
        super(BaseIdentityV2AdminTest, cls).setup_clients()
        cls.client = cls.os_admin.identity_client
        cls.non_admin_client = cls.os_primary.identity_client
        cls.token_client = cls.os_admin.token_client
        cls.tenants_client = cls.os_admin.tenants_client
        cls.non_admin_tenants_client = cls.os_primary.tenants_client
        cls.roles_client = cls.os_admin.roles_client
        cls.non_admin_roles_client = cls.os_primary.roles_client
        cls.users_client = cls.os_admin.users_client
        cls.non_admin_users_client = cls.os_primary.users_client
        cls.services_client = cls.os_admin.identity_services_client
        cls.endpoints_client = cls.os_admin.endpoints_client

    @classmethod
    def resource_setup(cls):
        super(BaseIdentityV2AdminTest, cls).resource_setup()
        cls.projects_client = cls.tenants_client

    def setup_test_user(self, password=None):
        """Set up a test user."""
        tenant = self.setup_test_tenant()
        user = self.create_test_user(tenantId=tenant['id'], password=password)
        return user

    def setup_test_tenant(self, **kwargs):
        """Set up a test tenant."""
        if 'name' not in kwargs:
            kwargs['name'] = data_utils.rand_name('test_tenant')
        if 'description' not in kwargs:
            kwargs['description'] = data_utils.rand_name('desc')
        tenant = self.projects_client.create_tenant(**kwargs)['tenant']
        # Delete the tenant at the end of the test
        self.addCleanup(
            test_utils.call_and_ignore_notfound_exc,
            self.tenants_client.delete_tenant, tenant['id'])
        return tenant


class BaseIdentityV3Test(BaseIdentityTest):

    credentials = ['primary']

    # identity v3 tests should obtain tokens and create accounts via v3
    # regardless of the configured CONF.identity.auth_version
    identity_version = 'v3'

    @classmethod
    def setup_clients(cls):
        super(BaseIdentityV3Test, cls).setup_clients()
        cls.non_admin_client = cls.os_primary.identity_v3_client
        cls.non_admin_users_client = cls.os_primary.users_v3_client
        cls.non_admin_token = cls.os_primary.token_v3_client
        cls.non_admin_projects_client = cls.os_primary.projects_client
        cls.non_admin_catalog_client = cls.os_primary.catalog_client
        cls.non_admin_versions_client =\
            cls.os_primary.identity_versions_v3_client
        cls.non_admin_app_creds_client = \
            cls.os_primary.application_credentials_client


class BaseIdentityV3AdminTest(BaseIdentityV3Test):

    credentials = ['primary', 'admin']

    # NOTE(andreaf) Identity tests work with credentials, so it is safer
    # for them to always use disposable credentials. Forcing dynamic creds
    # on regular identity tests would be however to restrictive, since it
    # would prevent any identity test from being executed against clouds where
    # admin credentials are not available.
    # Since All admin tests require admin credentials to be
    # executed, so this will not impact the ability to execute tests.
    force_tenant_isolation = True

    @classmethod
    def setup_clients(cls):
        super(BaseIdentityV3AdminTest, cls).setup_clients()
        cls.client = cls.os_admin.identity_v3_client
        cls.domains_client = cls.os_admin.domains_client
        cls.users_client = cls.os_admin.users_v3_client
        cls.trusts_client = cls.os_admin.trusts_client
        cls.roles_client = cls.os_admin.roles_v3_client
        cls.inherited_roles_client = cls.os_admin.inherited_roles_client
        cls.token = cls.os_admin.token_v3_client
        cls.endpoints_client = cls.os_admin.endpoints_v3_client
        cls.regions_client = cls.os_admin.regions_client
        cls.services_client = cls.os_admin.identity_services_v3_client
        cls.policies_client = cls.os_admin.policies_client
        cls.creds_client = cls.os_admin.credentials_client
        cls.groups_client = cls.os_admin.groups_client
        cls.projects_client = cls.os_admin.projects_client
        cls.role_assignments = cls.os_admin.role_assignments_client
        cls.oauth_consumers_client = cls.os_admin.oauth_consumers_client
        cls.oauth_token_client = cls.os_admin.oauth_token_client
        cls.domain_config_client = cls.os_admin.domain_config_client
        cls.endpoint_filter_client = cls.os_admin.endpoint_filter_client
        cls.endpoint_groups_client = cls.os_admin.endpoint_groups_client
        cls.project_tags_client = cls.os_admin.project_tags_client

        if CONF.identity.admin_domain_scope:
            # NOTE(andreaf) When keystone policy requires it, the identity
            # admin clients for these tests shall use 'domain' scoped tokens.
            # As the client manager is already created by the base class,
            # we set the scope for the inner auth provider.
            cls.os_admin.auth_provider.scope = 'domain'

    @classmethod
    def disable_user(cls, user_name, domain_id=None):
        user = cls.get_user_by_name(user_name, domain_id)
        cls.users_client.update_user(user['id'], name=user_name, enabled=False)

    @classmethod
    def create_domain(cls, **kwargs):
        """Create a domain."""
        if 'name' not in kwargs:
            kwargs['name'] = data_utils.rand_name('test_domain')
        if 'description' not in kwargs:
            kwargs['description'] = data_utils.rand_name('desc')
        domain = cls.domains_client.create_domain(**kwargs)['domain']
        cls.addClassResourceCleanup(test_utils.call_and_ignore_notfound_exc,
                                    cls.delete_domain, domain['id'])
        return domain

    @classmethod
    def delete_domain(cls, domain_id):
        # NOTE(mpavlase) It is necessary to disable the domain before deleting
        # otherwise it raises Forbidden exception
        cls.domains_client.update_domain(domain_id, enabled=False)
        cls.domains_client.delete_domain(domain_id)

    def setup_test_user(self, password=None):
        """Set up a test user."""
        project = self.setup_test_project()
        user = self.create_test_user(project_id=project['id'],
                                     password=password)
        return user

    def setup_test_project(self, **kwargs):
        """Set up a test project."""
        if 'name' not in kwargs:
            kwargs['name'] = data_utils.rand_name('test_project')
        if 'description' not in kwargs:
            kwargs['description'] = data_utils.rand_name('test_description')
        project = self.projects_client.create_project(**kwargs)['project']
        # Delete the project at the end of the test
        self.addCleanup(
            test_utils.call_and_ignore_notfound_exc,
            self.projects_client.delete_project, project['id'])
        return project

    def setup_test_domain(self):
        """Set up a test domain."""
        domain = self.create_domain()
        # Delete the domain at the end of the test
        self.addCleanup(
            test_utils.call_and_ignore_notfound_exc,
            self.delete_domain, domain['id'])
        return domain

    def setup_test_group(self, **kwargs):
        """Set up a test group."""
        if 'name' not in kwargs:
            kwargs['name'] = data_utils.rand_name(
                self.__class__.__name__ + '_test_project')
        if 'description' not in kwargs:
            kwargs['description'] = data_utils.rand_name(
                self.__class__.__name__ + '_test_description')
        group = self.groups_client.create_group(**kwargs)['group']
        self.addCleanup(
            test_utils.call_and_ignore_notfound_exc,
            self.groups_client.delete_group, group['id'])
        return group


class BaseApplicationCredentialsV3Test(BaseIdentityV3Test):

    @classmethod
    def skip_checks(cls):
        super(BaseApplicationCredentialsV3Test, cls).skip_checks()
        if not CONF.identity_feature_enabled.application_credentials:
            raise cls.skipException("Application credentials are not available"
                                    " in this environment")

    @classmethod
    def resource_setup(cls):
        super(BaseApplicationCredentialsV3Test, cls).resource_setup()
        cls.user_id = cls.os_primary.credentials.user_id
        cls.project_id = cls.os_primary.credentials.project_id

    def create_application_credential(self, name=None, **kwargs):
        name = name or data_utils.rand_name('application_credential')
        application_credential = (
            self.non_admin_app_creds_client.create_application_credential(
                self.user_id, name=name, **kwargs))['application_credential']
        self.addCleanup(
            self.non_admin_app_creds_client.delete_application_credential,
            self.user_id,
            application_credential['id'])
        return application_credential

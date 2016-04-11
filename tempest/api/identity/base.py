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

from oslo_log import log as logging

from tempest.common.utils import data_utils
from tempest import config
from tempest.lib import exceptions as lib_exc
import tempest.test

CONF = config.CONF
LOG = logging.getLogger(__name__)


class BaseIdentityTest(tempest.test.BaseTestCase):

    @classmethod
    def disable_user(cls, user_name):
        user = cls.get_user_by_name(user_name)
        cls.users_client.enable_disable_user(user['id'], enabled=False)

    @classmethod
    def disable_tenant(cls, tenant_name):
        tenant = cls.get_tenant_by_name(tenant_name)
        cls.tenants_client.update_tenant(tenant['id'], enabled=False)

    @classmethod
    def get_user_by_name(cls, name, domain_id=None):
        if domain_id:
            params = {'domain_id': domain_id}
            users = cls.users_client.list_users(params)['users']
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

    @classmethod
    def resource_setup(cls):
        super(BaseIdentityV2Test, cls).resource_setup()

    @classmethod
    def resource_cleanup(cls):
        super(BaseIdentityV2Test, cls).resource_cleanup()


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
        cls.data = DataGeneratorV2(cls.tenants_client, cls.users_client,
                                   cls.roles_client)

    @classmethod
    def resource_cleanup(cls):
        cls.data.teardown_all()
        super(BaseIdentityV2AdminTest, cls).resource_cleanup()


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

    @classmethod
    def resource_cleanup(cls):
        super(BaseIdentityV3Test, cls).resource_cleanup()


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

    @classmethod
    def resource_setup(cls):
        super(BaseIdentityV3AdminTest, cls).resource_setup()
        cls.data = DataGeneratorV3(cls.projects_client, cls.users_client,
                                   cls.roles_client, cls.domains_client)

    @classmethod
    def resource_cleanup(cls):
        cls.data.teardown_all()
        super(BaseIdentityV3AdminTest, cls).resource_cleanup()

    @classmethod
    def disable_user(cls, user_name, domain_id=None):
        user = cls.get_user_by_name(user_name, domain_id)
        cls.users_client.update_user(user['id'], user_name, enabled=False)

    def delete_domain(self, domain_id):
        # NOTE(mpavlase) It is necessary to disable the domain before deleting
        # otherwise it raises Forbidden exception
        self.domains_client.update_domain(domain_id, enabled=False)
        self.domains_client.delete_domain(domain_id)


class BaseDataGenerator(object):

    def __init__(self, projects_client, users_client, roles_client,
                 domains_client=None):
        self.projects_client = projects_client
        self.users_client = users_client
        self.roles_client = roles_client
        self.domains_client = domains_client

        self.user_password = None
        self.user = None
        self.tenant = None
        self.project = None
        self.role = None
        self.domain = None

        self.users = []
        self.tenants = []
        self.projects = []
        self.roles = []
        self.domains = []

    def _create_test_user(self, **kwargs):
        username = data_utils.rand_name('test_user')
        self.user_password = data_utils.rand_password()
        self.user = self.users_client.create_user(
            username, password=self.user_password,
            email=username + '@testmail.tm', **kwargs)['user']
        self.users.append(self.user)

    def setup_test_role(self):
        """Set up a test role."""
        self.role = self.roles_client.create_role(
            name=data_utils.rand_name('test_role'))['role']
        self.roles.append(self.role)

    @staticmethod
    def _try_wrapper(func, item, **kwargs):
        try:
            func(item['id'], **kwargs)
        except lib_exc.NotFound:
            pass
        except Exception:
            LOG.exception("Unexpected exception occurred in %s deletion. "
                          "But ignored here." % item['id'])

    def teardown_all(self):
        for user in self.users:
            self._try_wrapper(self.users_client.delete_user, user)
        for tenant in self.tenants:
            self._try_wrapper(self.projects_client.delete_tenant, tenant)
        for project in self.projects:
            self._try_wrapper(self.projects_client.delete_project, project)
        for role in self.roles:
            self._try_wrapper(self.roles_client.delete_role, role)
        for domain in self.domains:
            self._try_wrapper(self.domains_client.update_domain, domain,
                              enabled=False)
            self._try_wrapper(self.domains_client.delete_domain, domain)


class DataGeneratorV2(BaseDataGenerator):

    def setup_test_user(self):
        """Set up a test user."""
        self.setup_test_tenant()
        self._create_test_user(tenant_id=self.tenant['id'])

    def setup_test_tenant(self):
        """Set up a test tenant."""
        self.tenant = self.projects_client.create_tenant(
            name=data_utils.rand_name('test_tenant'),
            description=data_utils.rand_name('desc'))['tenant']
        self.tenants.append(self.tenant)


class DataGeneratorV3(BaseDataGenerator):

    def setup_test_user(self):
        """Set up a test user."""
        self.setup_test_project()
        self._create_test_user(project_id=self.project['id'])

    def setup_test_project(self):
        """Set up a test project."""
        self.project = self.projects_client.create_project(
            name=data_utils.rand_name('test_project'),
            description=data_utils.rand_name('desc'))['project']
        self.projects.append(self.project)

    def setup_test_domain(self):
        """Set up a test domain."""
        self.domain = self.domains_client.create_domain(
            name=data_utils.rand_name('test_domain'),
            description=data_utils.rand_name('desc'))['domain']
        self.domains.append(self.domain)

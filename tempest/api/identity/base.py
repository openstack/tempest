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
from tempest_lib.common.utils import data_utils
from tempest_lib import exceptions as lib_exc

from tempest import clients
from tempest.common import cred_provider
from tempest.common import credentials
from tempest import config
import tempest.test

CONF = config.CONF
LOG = logging.getLogger(__name__)


class BaseIdentityTest(tempest.test.BaseTestCase):

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
        users = cls.client.get_users()
        user = [u for u in users if u['name'] == name]
        if len(user) > 0:
            return user[0]

    @classmethod
    def get_tenant_by_name(cls, name):
        try:
            tenants = cls.client.list_tenants()
        except AttributeError:
            tenants = cls.client.list_projects()
        tenant = [t for t in tenants if t['name'] == name]
        if len(tenant) > 0:
            return tenant[0]

    @classmethod
    def get_role_by_name(cls, name):
        roles = cls.client.list_roles()
        role = [r for r in roles if r['name'] == name]
        if len(role) > 0:
            return role[0]


class BaseIdentityV2Test(BaseIdentityTest):

    @classmethod
    def setup_credentials(cls):
        super(BaseIdentityV2Test, cls).setup_credentials()
        cls.os = cls.get_client_manager(identity_version='v2')

    @classmethod
    def skip_checks(cls):
        super(BaseIdentityV2Test, cls).skip_checks()
        if not CONF.identity_feature_enabled.api_v2:
            raise cls.skipException("Identity api v2 is not enabled")

    @classmethod
    def setup_clients(cls):
        super(BaseIdentityV2Test, cls).setup_clients()
        cls.non_admin_client = cls.os.identity_client
        cls.non_admin_token_client = cls.os.token_client

    @classmethod
    def resource_setup(cls):
        super(BaseIdentityV2Test, cls).resource_setup()

    @classmethod
    def resource_cleanup(cls):
        super(BaseIdentityV2Test, cls).resource_cleanup()


class BaseIdentityV2AdminTest(BaseIdentityV2Test):

    @classmethod
    def setup_credentials(cls):
        super(BaseIdentityV2AdminTest, cls).setup_credentials()
        cls.os_adm = clients.Manager(cls.isolated_creds.get_admin_creds())

    @classmethod
    def skip_checks(cls):
        if not credentials.is_admin_available():
            raise cls.skipException('v2 Admin auth disabled')
        super(BaseIdentityV2AdminTest, cls).skip_checks()

    @classmethod
    def setup_clients(cls):
        super(BaseIdentityV2AdminTest, cls).setup_clients()
        cls.client = cls.os_adm.identity_client
        cls.token_client = cls.os_adm.token_client
        if not cls.client.has_admin_extensions():
            raise cls.skipException("Admin extensions disabled")

    @classmethod
    def resource_setup(cls):
        super(BaseIdentityV2AdminTest, cls).resource_setup()
        cls.data = DataGenerator(cls.client)

    @classmethod
    def resource_cleanup(cls):
        cls.data.teardown_all()
        super(BaseIdentityV2AdminTest, cls).resource_cleanup()


class BaseIdentityV3Test(BaseIdentityTest):

    @classmethod
    def setup_credentials(cls):
        super(BaseIdentityV3Test, cls).setup_credentials()
        cls.os = cls.get_client_manager(identity_version='v3')

    @classmethod
    def skip_checks(cls):
        super(BaseIdentityV3Test, cls).skip_checks()
        if not CONF.identity_feature_enabled.api_v3:
            raise cls.skipException("Identity api v3 is not enabled")

    @classmethod
    def setup_clients(cls):
        super(BaseIdentityV3Test, cls).setup_clients()
        cls.non_admin_client = cls.os.identity_v3_client
        cls.non_admin_token = cls.os.token_v3_client
        cls.non_admin_endpoints_client = cls.os.endpoints_client
        cls.non_admin_region_client = cls.os.region_client
        cls.non_admin_service_client = cls.os.service_client
        cls.non_admin_policy_client = cls.os.policy_client
        cls.non_admin_creds_client = cls.os.credentials_client

    @classmethod
    def resource_cleanup(cls):
        super(BaseIdentityV3Test, cls).resource_cleanup()


class BaseIdentityV3AdminTest(BaseIdentityV3Test):

    @classmethod
    def setup_credentials(cls):
        super(BaseIdentityV3AdminTest, cls).setup_credentials()
        cls.os_adm = clients.Manager(cls.isolated_creds.get_admin_creds())

    @classmethod
    def skip_checks(cls):
        if not credentials.is_admin_available():
            raise cls.skipException('v3 Admin auth disabled')
        super(BaseIdentityV3AdminTest, cls).skip_checks()

    @classmethod
    def setup_clients(cls):
        super(BaseIdentityV3AdminTest, cls).setup_clients()
        cls.client = cls.os_adm.identity_v3_client
        cls.token = cls.os_adm.token_v3_client
        cls.endpoints_client = cls.os_adm.endpoints_client
        cls.region_client = cls.os_adm.region_client
        cls.data = DataGenerator(cls.client)
        cls.service_client = cls.os_adm.service_client
        cls.policy_client = cls.os_adm.policy_client
        cls.creds_client = cls.os_adm.credentials_client

    @classmethod
    def resource_cleanup(cls):
        cls.data.teardown_all()
        super(BaseIdentityV3AdminTest, cls).resource_cleanup()

    @classmethod
    def get_user_by_name(cls, name):
        users = cls.client.get_users()
        user = [u for u in users if u['name'] == name]
        if len(user) > 0:
            return user[0]

    @classmethod
    def get_tenant_by_name(cls, name):
        tenants = cls.client.list_projects()
        tenant = [t for t in tenants if t['name'] == name]
        if len(tenant) > 0:
            return tenant[0]

    @classmethod
    def get_role_by_name(cls, name):
        roles = cls.client.list_roles()
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
            self.domains = []

        @property
        def test_credentials(self):
            return cred_provider.get_credentials(username=self.test_user,
                                                 user_id=self.user['id'],
                                                 password=self.test_password,
                                                 tenant_name=self.test_tenant,
                                                 tenant_id=self.tenant['id'])

        def setup_test_user(self):
            """Set up a test user."""
            self.setup_test_tenant()
            self.test_user = data_utils.rand_name('test_user')
            self.test_password = data_utils.rand_name('pass')
            self.test_email = self.test_user + '@testmail.tm'
            self.user = self.client.create_user(self.test_user,
                                                self.test_password,
                                                self.tenant['id'],
                                                self.test_email)
            self.users.append(self.user)

        def setup_test_tenant(self):
            """Set up a test tenant."""
            self.test_tenant = data_utils.rand_name('test_tenant')
            self.test_description = data_utils.rand_name('desc')
            self.tenant = self.client.create_tenant(
                name=self.test_tenant,
                description=self.test_description)
            self.tenants.append(self.tenant)

        def setup_test_role(self):
            """Set up a test role."""
            self.test_role = data_utils.rand_name('role')
            self.role = self.client.create_role(self.test_role)
            self.roles.append(self.role)

        def setup_test_v3_user(self):
            """Set up a test v3 user."""
            self.setup_test_project()
            self.test_user = data_utils.rand_name('test_user')
            self.test_password = data_utils.rand_name('pass')
            self.test_email = self.test_user + '@testmail.tm'
            self.v3_user = self.client.create_user(
                self.test_user,
                password=self.test_password,
                project_id=self.project['id'],
                email=self.test_email)
            self.v3_users.append(self.v3_user)

        def setup_test_project(self):
            """Set up a test project."""
            self.test_project = data_utils.rand_name('test_project')
            self.test_description = data_utils.rand_name('desc')
            self.project = self.client.create_project(
                name=self.test_project,
                description=self.test_description)
            self.projects.append(self.project)

        def setup_test_v3_role(self):
            """Set up a test v3 role."""
            self.test_role = data_utils.rand_name('role')
            self.v3_role = self.client.create_role(self.test_role)
            self.v3_roles.append(self.v3_role)

        def setup_test_domain(self):
            """Set up a test domain."""
            self.test_domain = data_utils.rand_name('test_domain')
            self.test_description = data_utils.rand_name('desc')
            self.domain = self.client.create_domain(
                name=self.test_domain,
                description=self.test_description)
            self.domains.append(self.domain)

        @staticmethod
        def _try_wrapper(func, item, **kwargs):
            try:
                if kwargs:
                    func(item['id'], **kwargs)
                else:
                    func(item['id'])
            except lib_exc.NotFound:
                pass
            except Exception:
                LOG.exception("Unexpected exception occurred in %s deletion."
                              " But ignored here." % item['id'])

        def teardown_all(self):
            # NOTE(masayukig): v3 client doesn't have v2 method.
            # (e.g. delete_tenant) So we need to check resources existence
            # before using client methods.
            for user in self.users:
                self._try_wrapper(self.client.delete_user, user)
            for tenant in self.tenants:
                self._try_wrapper(self.client.delete_tenant, tenant)
            for role in self.roles:
                self._try_wrapper(self.client.delete_role, role)
            for v3_user in self.v3_users:
                self._try_wrapper(self.client.delete_user, v3_user)
            for v3_project in self.projects:
                self._try_wrapper(self.client.delete_project, v3_project)
            for v3_role in self.v3_roles:
                self._try_wrapper(self.client.delete_role, v3_role)
            for domain in self.domains:
                self._try_wrapper(self.client.update_domain, domain,
                                  enabled=False)
                self._try_wrapper(self.client.delete_domain, domain)
